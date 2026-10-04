"""Explicit password -> challenge -> session flow; refresh never replays business HTTP."""

import hmac
import secrets
from uuid import uuid4

import pyotp
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from framework_lab.models import Audit, AuthSession, Challenge, RefreshToken, User
from framework_lab.security import (
    PolicyError,
    digest,
    dummy_password_hash,
    otp_digest,
    passwords,
    totp_step,
)


def audit(db, user_id: str, event: str, correlation_id: str) -> None:
    db.add(Audit(id=str(uuid4()), user_id=user_id, event=event, correlation_id=correlation_id))


class AuthService:
    def __init__(self, settings, jwt_policy, email_delivery, sms_delivery=None):
        self.settings, self.jwt = settings, jwt_policy
        self.email_delivery, self.sms_delivery = email_delivery, sms_delivery

    def register(self, db, body, correlation_id):
        if body.mfa_method == "sms" and self.sms_delivery is None:
            raise PolicyError(422, "sms_adapter_unavailable")
        user = User(
            id=str(uuid4()),
            tenant_id=str(uuid4()),
            email=body.email,
            password_hash=passwords.hash(body.password.get_secret_value()),
            mfa_method=body.mfa_method,
            totp_secret=pyotp.random_base32() if body.mfa_method == "totp" else None,
        )
        db.add(user)
        try:
            db.flush()
            audit(db, user.id, "registered", correlation_id)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise PolicyError(409, "registration_conflict") from None
        return {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "mfa_method": user.mfa_method,
            "totp_secret": user.totp_secret,
        }

    def login(self, db, body, correlation_id):
        now = int(self.jwt.clock())
        user = db.scalar(select(User).where(User.email == body.email).with_for_update())
        supplied = body.password.get_secret_value()
        valid = passwords.verify(supplied, user.password_hash if user else dummy_password_hash)
        if user is None:
            raise PolicyError(401, "invalid_credentials")
        if user.locked_until > now:
            raise PolicyError(429, "login_locked", user.locked_until - now)
        if not valid:
            db.execute(
                update(User).where(User.id == user.id).values(failed_logins=User.failed_logins + 1)
            )
            db.refresh(user)
            if user.failed_logins >= 3:
                user.locked_until = now + 30
            audit(db, user.id, "password_rejected", correlation_id)
            db.commit()
            raise PolicyError(401, "invalid_credentials")
        user.failed_logins = 0
        user.locked_until = 0
        # Only the newest password-authenticated challenge may complete.
        db.execute(update(Challenge).where(Challenge.user_id == user.id).values(consumed=True))
        challenge_id = str(uuid4())
        code = f"{secrets.randbelow(1_000_000):06d}" if user.mfa_method != "totp" else None
        challenge = Challenge(
            id=challenge_id,
            user_id=user.id,
            expires_at=now + self.settings.challenge_seconds,
            code_hash=otp_digest(self.settings.signing_key, challenge_id, code) if code else None,
        )
        db.add(challenge)
        audit(db, user.id, "challenge_issued", correlation_id)
        db.commit()
        if code is not None:
            delivery = self.email_delivery if user.mfa_method == "email" else self.sms_delivery
            try:
                delivery.send(user.email, challenge_id, code)
            except Exception:
                # Invalidate the challenge and return a safe, distinct delivery failure.
                challenge.consumed = True
                audit(db, user.id, "delivery_failed", correlation_id)
                db.commit()
                raise PolicyError(503, "otp_delivery_unavailable") from None
        return {
            "challenge_id": challenge_id,
            "method": user.mfa_method,
            "expires_in": self.settings.challenge_seconds,
        }

    def verify(self, db, body, correlation_id):
        preliminary = db.get(Challenge, body.challenge_id)
        if preliminary is None:
            raise PolicyError(401, "invalid_challenge")
        # Match login's user -> challenge lock order, including the FK insert below.
        user = db.scalar(select(User).where(User.id == preliminary.user_id).with_for_update())
        challenge = db.scalar(
            select(Challenge)
            .where(Challenge.id == body.challenge_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        now = int(self.jwt.clock())
        if challenge is None or challenge.consumed or now >= challenge.expires_at:
            raise PolicyError(401, "invalid_challenge")
        if challenge.attempts >= self.settings.max_otp_attempts:
            raise PolicyError(429, "challenge_locked", max(1, challenge.expires_at - now))
        code = body.code.get_secret_value()
        step = totp_step(user.totp_secret, code, now) if user.mfa_method == "totp" else None
        valid = (
            (step is not None and step > user.last_totp_step)
            if user.mfa_method == "totp"
            else hmac.compare_digest(
                otp_digest(self.settings.signing_key, challenge.id, code),
                challenge.code_hash,
            )
        )
        if not valid:
            db.execute(
                update(Challenge)
                .where(Challenge.id == challenge.id)
                .values(attempts=Challenge.attempts + 1)
            )
            audit(db, user.id, "otp_rejected", correlation_id)
            db.commit()
            raise PolicyError(401, "invalid_otp")
        claimed = db.execute(
            update(Challenge)
            .where(
                Challenge.id == challenge.id,
                Challenge.consumed.is_(False),
                Challenge.attempts < self.settings.max_otp_attempts,
            )
            .values(consumed=True)
        ).rowcount
        if claimed != 1:
            db.rollback()
            raise PolicyError(401, "invalid_challenge")
        if step is not None:
            accepted = db.execute(
                update(User)
                .where(
                    User.id == user.id,
                    User.last_totp_step < step,
                )
                .values(last_totp_step=step)
            ).rowcount
            if accepted != 1:
                db.rollback()
                raise PolicyError(401, "invalid_otp")
        session = AuthSession(
            id=str(uuid4()),
            user_id=user.id,
            refresh_hash="",
            expires_at=now + self.settings.refresh_seconds,
        )
        db.add(session)
        db.flush()
        tokens = self._tokens(db, session)
        audit(db, user.id, "mfa_completed", correlation_id)
        db.commit()
        return tokens

    def _tokens(self, db, session):
        refresh = f"{session.id}.{secrets.token_urlsafe(32)}"
        session.refresh_hash = digest(refresh)
        db.add(RefreshToken(token_hash=session.refresh_hash, session_id=session.id))
        return {
            "access_token": self.jwt.issue(session.user_id, session.id),
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": self.settings.access_seconds,
        }

    def refresh(self, db, body, correlation_id):
        supplied = body.refresh_token.get_secret_value()
        token = db.get(RefreshToken, digest(supplied))
        if token is None:
            raise PolicyError(401, "invalid_refresh")
        session = db.scalar(
            select(AuthSession).where(AuthSession.id == token.session_id).with_for_update()
        )
        if session.revoked or int(self.jwt.clock()) >= session.expires_at:
            raise PolicyError(401, "invalid_refresh")
        claimed = db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token.token_hash,
                RefreshToken.used.is_(False),
            )
            .values(used=True)
        ).rowcount
        if claimed != 1:
            session.revoked = True
            audit(db, session.user_id, "refresh_reuse_revoked", correlation_id)
            db.commit()
            raise PolicyError(401, "refresh_reuse")
        tokens = self._tokens(db, session)
        audit(db, session.user_id, "refresh_rotated", correlation_id)
        db.commit()
        return tokens

    def identity(self, db, token):
        claims = self.jwt.verify(token)
        session = db.get(AuthSession, claims["sid"])
        if session is None or session.revoked or session.user_id != claims["sub"]:
            raise PolicyError(401, "unauthorized")
        if int(self.jwt.clock()) >= session.expires_at:
            raise PolicyError(401, "unauthorized")
        return db.get(User, session.user_id), session
