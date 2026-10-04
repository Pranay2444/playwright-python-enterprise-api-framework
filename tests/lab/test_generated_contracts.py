import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import func, select

from framework_lab.models import User

pytestmark = [
    pytest.mark.lab,
    pytest.mark.property,
    pytest.mark.contract,
    pytest.mark.domain("contracts"),
]


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(st.one_of(st.integers(), st.booleans(), st.lists(st.integers(), max_size=3)))
def test_generated_wrong_password_types_are_rejected_without_user_creation(lab, password):
    # Reuse this test's isolated DB only for rejected requests; no accepted shared state.
    response = lab.api.post(
        "/auth/register",
        data={
            "email": "generated@example.test",
            "password": password,
            "mfa_method": "email",
        },
    )
    assert response.status == 422
    with lab.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0
