import pytest

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.dummyjson.auth_client import AuthClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.config import Settings
from api_framework.contracts.validation import contract_json

pytestmark = pytest.mark.contract


@pytest.mark.smoke
def test_login_returns_tokens(auth_client: AuthClient, settings: Settings) -> None:
    result = contract_json(auth_client.login(settings.username, settings.password), "login")
    assert result["username"] == settings.username
    assert isinstance(result["id"], int) and result["id"] > 0
    assert isinstance(result.get("accessToken"), str) and bool(result["accessToken"])
    assert isinstance(result.get("refreshToken"), str) and bool(result["refreshToken"])


@pytest.mark.smoke
def test_authenticated_user(users_client: UsersClient, settings: Settings) -> None:
    result = contract_json(users_client.me(), "user")
    assert result["username"] == settings.username
    assert isinstance(result["id"], int) and result["id"] > 0


@pytest.mark.regression
def test_refreshed_token_authenticates_same_user(
    token_manager: TokenManager, users_client: UsersClient
) -> None:
    before = contract_json(users_client.me(), "user")
    token_manager.refresh()
    after = contract_json(users_client.me(), "user")
    assert after["id"] == before["id"]
    assert after["username"] == before["username"]
    # JWTs issued within the same second may match; token inequality is not a requirement.
