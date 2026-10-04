from types import SimpleNamespace

import pytest

from api_framework.auth.lab_session import AuthFlowError, LabSession


class FakeResponse:
    headers = {"content-type": "application/json"}

    def __init__(self, status, body):
        self.status, self.body = status, body

    def json(self):
        return self.body


def test_session_clears_on_bad_provider_bad_tokens_and_failed_refresh():
    tokens = {
        "access_token": "access",
        "refresh_token": "refresh",
        "expires_in": 10,
        "token_type": "bearer",
    }
    client = SimpleNamespace(
        login=lambda *_args: FakeResponse(202, {"challenge_id": "challenge"}),
        verify=lambda *_args: FakeResponse(200, tokens),
        refresh=lambda *_args: FakeResponse(401, {"error": "invalid_refresh"}),
    )
    session = LabSession(client)
    session.authenticate("synthetic", "private-password", lambda _challenge: "123456")
    assert "access" not in repr(session) and "refresh" not in repr(session)
    with pytest.raises(AuthFlowError, match="session cleared"):
        session.refresh()
    assert session.state == "anonymous"
    tokens["access_token"] = "bad\nheader"
    with pytest.raises(AuthFlowError):
        session.authenticate("synthetic", "private-password", lambda _challenge: "123456")
    assert session.state == "anonymous"

    def failed_provider(_challenge):
        raise RuntimeError("private-provider-key")

    with pytest.raises(AuthFlowError) as error:
        session.authenticate("synthetic", "private-password", failed_provider)
    assert "private-provider-key" not in str(error.value)


def test_logout_failure_clears_client_but_remains_visible():
    client = SimpleNamespace(logout=lambda _headers: FakeResponse(503, {}))
    session = LabSession(client)
    session._accept(
        {
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": 10,
            "token_type": "bearer",
        }
    )
    with pytest.raises(AuthFlowError, match="Server logout failed"):
        session.logout()
    assert session.state == "anonymous"
