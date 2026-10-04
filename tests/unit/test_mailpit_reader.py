from types import SimpleNamespace
from uuid import uuid4

import pytest

from api_framework.auth.mailpit import MailpitCodeReader


def response(body):
    return SimpleNamespace(
        status=200, headers={"content-type": "application/json"}, json=lambda: body
    )


def test_reader_requires_recipient_subject_and_body_correlation():
    challenge, matching_id = str(uuid4()), str(uuid4())
    calls = []

    def get(path, **_kwargs):
        calls.append(path)
        if path == "/api/v1/search":
            return response(
                {
                    "messages": [
                        {
                            "ID": str(uuid4()),
                            "Subject": f"Lab sign-in {challenge}",
                            "To": [{"Address": "other@example.test"}],
                        },
                        {
                            "ID": str(uuid4()),
                            "Subject": "Other challenge",
                            "To": [{"Address": "qa@example.test"}],
                        },
                        {
                            "ID": matching_id,
                            "Subject": f"Lab sign-in {challenge}",
                            "To": [{"Address": "qa@example.test"}],
                        },
                    ]
                }
            )
        assert path == f"/api/v1/message/{matching_id}"
        return response({"Text": f"Challenge: {challenge}\nCode: 123456\n"})

    reader = MailpitCodeReader(SimpleNamespace(get=get), "qa@example.test")
    assert reader(challenge) == "123456"
    assert len(calls) == 2


def test_reader_timeout_never_returns_uncorrelated_code(monkeypatch):
    times = iter((0, 2))
    monkeypatch.setattr("api_framework.auth.mailpit.time.monotonic", lambda: next(times))
    reader = MailpitCodeReader(
        SimpleNamespace(get=lambda *_args, **_kwargs: response({"messages": []})),
        "qa@example.test",
        1,
    )
    with pytest.raises(RuntimeError, match="before the deadline"):
        reader(str(uuid4()))


def test_reader_rejects_unsafe_challenge_before_http():
    reader = MailpitCodeReader(
        SimpleNamespace(get=lambda *_args: pytest.fail("HTTP must not run")), "qa@example.test"
    )
    with pytest.raises(ValueError):
        reader("../message")
