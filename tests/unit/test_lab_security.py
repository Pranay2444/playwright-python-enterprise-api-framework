from dataclasses import replace

import jwt
import pyotp
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from framework_lab.schemas import Registration
from framework_lab.security import JwtPolicy, PolicyError, safe_filename, totp_step
from framework_lab.settings import LabSettings

pytestmark = [pytest.mark.auth, pytest.mark.security, pytest.mark.domain("authentication")]


@pytest.fixture
def policy():
    return JwtPolicy(
        LabSettings("sqlite:///unused.db", "synthetic-test-signing-key-" * 2), lambda: 1800000010
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"exp": 1800000010},
        {"nbf": 1800000011},
        {"iat": 1800000011},
        {"iss": "other"},
        {"aud": "other"},
        {"sub": ""},
        {"sid": ""},
        {"kind": "refresh"},
        {"exp": True},
        {"iat": "1800000010"},
    ],
)
def test_jwt_claim_policy_rejects_invalid_claims(policy, mutation):
    token = policy.issue("user", "session")
    claims = jwt.decode(token, options={"verify_signature": False})
    claims.update(mutation)
    invalid = jwt.encode(claims, policy.settings.signing_key, algorithm="HS256")
    with pytest.raises(PolicyError, match="unauthorized"):
        policy.verify(invalid)


@pytest.mark.parametrize("algorithm", ["none", "HS384"])
def test_jwt_rejects_unapproved_algorithm(policy, algorithm):
    claims = jwt.decode(policy.issue("user", "session"), options={"verify_signature": False})
    invalid = jwt.encode(
        claims, "" if algorithm == "none" else policy.settings.signing_key, algorithm=algorithm
    )
    with pytest.raises(PolicyError):
        policy.verify(invalid)


def test_jwt_signature_and_missing_claims(policy):
    for claims, key in [
        ({"sub": "user"}, policy.settings.signing_key),
        (
            jwt.decode(policy.issue("user", "session"), options={"verify_signature": False}),
            "other-synthetic-key-" * 3,
        ),
    ]:
        with pytest.raises(PolicyError):
            policy.verify(jwt.encode(claims, key, algorithm="HS256"))
    assert policy.verify(policy.issue("user", "session"))["sub"] == "user"


def test_totp_time_boundary_and_adjacent_steps():
    secret = "JBSWY3DPEHPK3PXP"  # Published synthetic unit-test seed only.
    otp = pyotp.TOTP(secret)
    assert totp_step(secret, otp.at(1800000029), 1800000029) == 1800000029 // 30
    assert totp_step(secret, otp.at(1800000029), 1800000030) is None
    assert totp_step(secret, otp.at(1800000060), 1800000030) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("signing_key", "short"),
        ("database_url", "mysql://private"),
        ("access_seconds", 0),
        ("upload_limit", True),
        ("refresh_seconds", 120),
    ],
)
def test_invalid_lab_settings_do_not_echo_secrets(field, value):
    base = LabSettings("sqlite:///unused.db", "private-test-key-" * 3)
    with pytest.raises(ValueError) as error:
        replace(base, **{field: value})
    assert "private-test-key" not in str(error.value)
    assert "private-test-key" not in repr(base)


@pytest.mark.property
@settings(max_examples=50, deadline=None, derandomize=True)
@given(
    st.one_of(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=30).map(
            lambda base: base + ".txt"
        ),
        st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=90),
    )
)
def test_accepted_filenames_cannot_escape_storage(name):
    try:
        safe_filename(name)
    except PolicyError:
        return
    assert "/" not in name and "\\" not in name and ".." not in name
    assert name.endswith(".txt") and name.isascii()


@pytest.mark.property
@settings(max_examples=30, derandomize=True)
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=20))
def test_registration_never_accepts_client_role(local_part):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Registration(
            email=f"{local_part}@example.test", password="synthetic-password", role="admin"
        )
