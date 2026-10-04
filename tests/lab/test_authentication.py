from uuid import uuid4

import pytest
from sqlalchemy import select

from api_framework.auth.lab_session import AuthFlowError
from api_framework.core.responses import json_object
from framework_lab.models import Challenge, User

pytestmark = [pytest.mark.lab, pytest.mark.auth, pytest.mark.domain("authentication")]


@pytest.mark.parametrize("method", ["email", "totp", "sms"])
def test_password_mfa_identity_and_logout(lab, method):
    user, session, _documents = lab.signed_in(method)
    assert json_object(lab.auth.me(session.headers()))["id"] == user["id"]
    old_header = session.headers()
    assert lab.probe.password_is_hashed(user["id"])
    session.logout()
    assert session.state == "anonymous"
    assert lab.auth.me(old_header).status == 401
    assert {"registered", "challenge_issued", "mfa_completed", "logged_out"} <= set(
        lab.probe.audit_events(user["id"])
    )


def test_password_step_never_issues_tokens(lab):
    _user, email, password = lab.register()
    body = json_object(lab.auth.login(email, password), 202)
    assert "access_token" not in body and "code" not in body
    assert lab.auth.me().status == 401


@pytest.mark.parametrize(
    "headers", [None, {"Authorization": "Basic synthetic"}, {"Authorization": "Bearer malformed"}]
)
def test_missing_or_invalid_access_is_401(lab, headers):
    response = lab.auth.me(headers)
    assert response.status == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expiry_refresh_rotation_and_reuse_revoke_family(lab):
    _user, session, _documents = lab.signed_in()
    old_access, old_refresh = session.headers(), session._refresh
    lab.clock.advance(120)
    assert lab.auth.me(old_access).status == 401
    with pytest.raises(AuthFlowError, match="refresh explicitly"):
        session.headers()
    session.refresh()
    assert json_object(lab.auth.me(session.headers()))["id"]
    current_access = session.headers()
    assert lab.auth.refresh(old_refresh).status == 401
    assert lab.auth.me(current_access).status == 401
    with pytest.raises(AuthFlowError, match="session cleared"):
        session.refresh()
    assert session.state == "anonymous"


def test_forged_refresh_does_not_revoke_legitimate_session(lab):
    _user, session, _documents = lab.signed_in()
    fake = session._refresh.split(".")[0] + ".not-a-real-refresh-secret"
    assert lab.auth.refresh(fake).status == 401
    assert lab.auth.me(session.headers()).status == 200


def test_refresh_absolute_expiry(lab):
    _user, session, _documents = lab.signed_in()
    lab.clock.advance(900)
    assert lab.auth.refresh(session._refresh).status == 401


def test_login_lockout_has_retry_after_and_clock_recovery(lab):
    _user, email, password = lab.register()
    for _ in range(3):
        assert lab.auth.login(email, "wrong-synthetic-password").status == 401
    response = lab.auth.login(email, password)
    assert response.status == 429 and response.headers["retry-after"] == "30"
    lab.clock.advance(30)
    assert lab.auth.login(email, password).status == 202


def test_unknown_account_and_wrong_password_share_safe_error(lab):
    _user, email, _password = lab.register()
    for name in (email, "unknown@example.test"):
        body = json_object(lab.auth.login(name, "wrong-synthetic-password"), 401)
        assert body["error"] == "invalid_credentials"
        assert name not in str(body)


def test_otp_attempt_budget_and_new_challenge(lab):
    user, email, password = lab.register()
    challenge = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    actual = lab.code_provider(user, email)(challenge)
    wrong = "111111" if actual != "111111" else "222222"
    for _ in range(3):
        assert lab.auth.verify(challenge, wrong).status == 401
    assert lab.auth.verify(challenge, actual).status == 429
    newer = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    assert lab.auth.verify(challenge, actual).status == 401
    assert lab.auth.verify(newer, lab.code_provider(user, email)(newer)).status == 200


@pytest.mark.parametrize("elapsed", [119, 120])
def test_email_otp_expiry_boundary(lab, elapsed):
    user, email, password = lab.register()
    challenge = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    code = lab.code_provider(user, email)(challenge)
    lab.clock.advance(elapsed)
    assert lab.auth.verify(challenge, code).status == (200 if elapsed == 119 else 401)


def test_consumed_otp_and_totp_step_cannot_be_replayed(lab):
    user, email, password = lab.register("totp")
    provider = lab.code_provider(user, email)
    first = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    code = provider(first)
    assert lab.auth.verify(first, code).status == 200
    assert lab.auth.verify(first, code).status == 401
    second = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    assert lab.auth.verify(second, code).status == 401
    lab.clock.advance(30)
    assert lab.auth.verify(second, provider(second)).status == 200


def test_wrong_recipient_code_does_not_complete_other_challenge(lab, monkeypatch):
    codes = iter((123456, 654321))
    monkeypatch.setattr("framework_lab.auth_service.secrets.randbelow", lambda _limit: next(codes))
    a, email_a, password_a = lab.register()
    _b, email_b, password_b = lab.register()
    ca = json_object(lab.auth.login(email_a, password_a), 202)["challenge_id"]
    cb = json_object(lab.auth.login(email_b, password_b), 202)["challenge_id"]
    code_a = lab.code_provider(a, email_a)(ca)
    assert lab.auth.verify(cb, code_a).status == 401


def test_delivery_failure_invalidates_challenge_without_secrets(lab):
    class BrokenDelivery:
        def send(self, *_args):
            raise RuntimeError("secret-transport-detail")

    lab.app.state.auth.email_delivery = BrokenDelivery()
    user, email, password = lab.register()
    response = lab.auth.login(email, password)
    assert response.status == 503 and "secret-transport-detail" not in response.text()
    with lab.app.state.sessions() as db:
        challenge = db.scalar(select(Challenge).where(Challenge.user_id == user["id"]))
        assert challenge.consumed


def test_signup_cannot_assign_admin_and_member_is_forbidden(lab):
    response = lab.api.post(
        "/auth/register",
        data={
            "email": "bad@example.test",
            "password": "synthetic-password",
            "role": "admin",
            "tenant_id": str(uuid4()),
        },
    )
    assert response.status == 422
    user, session, _documents = lab.signed_in()
    assert lab.api.request("GET", "/auth/admin/audit", headers=session.headers()).status == 403
    # Admin provisioning is a test-owned DB seam, never a public registration field.
    with lab.app.state.sessions() as db:
        db.get(User, user["id"]).role = "admin"
        db.commit()
    assert lab.api.request("GET", "/auth/admin/audit", headers=session.headers()).status == 200


def test_duplicate_registration_and_redacted_validation(lab):
    _user, email, password = lab.register()
    assert lab.auth.register(email, password).status == 409
    response = lab.auth.register("not-an-email", "private-short")
    assert response.status == 422 and "private-short" not in response.text()
    assert json_object(response, 422)["correlation_id"] == response.headers["x-correlation-id"]
