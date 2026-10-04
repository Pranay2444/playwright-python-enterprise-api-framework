"""Server policies. Inject a clock instead of disabling expiry checks in tests."""

import hashlib
import hmac
import re
import time
from collections.abc import Callable
from uuid import uuid4

import jwt
import pyotp
from pwdlib import PasswordHash

from framework_lab.settings import LabSettings

passwords = PasswordHash.recommended()
# Hash once, verify this on unknown accounts to avoid the simplest timing oracle.
dummy_password_hash = passwords.hash("synthetic-dummy-password-only")


class PolicyError(Exception):
    def __init__(self, status: int, code: str, retry_after: int | None = None):
        self.status = status
        self.code = code
        self.retry_after = retry_after
        super().__init__(code)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def otp_digest(key: str, challenge_id: str, code: str) -> str:
    # A keyed digest protects a six-digit OTP from offline enumeration without the key.
    return hmac.new(key.encode(), f"{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()


def safe_filename(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,75}\.txt", name) or ".." in name:
        raise PolicyError(422, "invalid_filename")
    return name


class JwtPolicy:
    def __init__(self, settings: LabSettings, clock: Callable[[], float] = time.time):
        self.settings = settings
        self.clock = clock

    def issue(self, user_id: str, session_id: str) -> str:
        now = int(self.clock())
        return jwt.encode(
            {
                "sub": user_id,
                "sid": session_id,
                "jti": str(uuid4()),
                "iss": self.settings.issuer,
                "aud": self.settings.audience,
                "iat": now,
                "nbf": now,
                "exp": now + self.settings.access_seconds,
                "kind": "access",
            },
            self.settings.signing_key,
            algorithm="HS256",
        )

    def verify(self, token: str) -> dict:
        try:
            claims = jwt.decode(
                token,
                self.settings.signing_key,
                algorithms=["HS256"],
                issuer=self.settings.issuer,
                audience=self.settings.audience,
                options={
                    "require": ["sub", "sid", "jti", "iss", "aud", "iat", "nbf", "exp", "kind"],
                    # Validate temporal claims below against the injected server clock.
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                },
            )
            now = int(self.clock())
            if any(type(claims[k]) is not int for k in ("iat", "nbf", "exp")):
                raise ValueError
            if claims["kind"] != "access" or not claims["nbf"] <= now < claims["exp"]:
                raise ValueError
            if claims["iat"] > now or claims["exp"] <= claims["iat"]:
                raise ValueError
            for key in ("sub", "sid", "jti"):
                if not isinstance(claims[key], str) or not claims[key]:
                    raise ValueError
            return claims
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise PolicyError(401, "unauthorized") from None


def totp_step(secret: str, code: str, now: int) -> int | None:
    # Current step only: no hidden acceptance of an old or future OTP.
    return now // 30 if pyotp.TOTP(secret).verify(code, for_time=now, valid_window=0) else None
