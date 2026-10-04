import pytest

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.dummyjson.auth_client import AuthClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.config import Settings
from api_framework.core.responses import json_object


@pytest.mark.smoke
def test_login_returns_tokens(auth_client: AuthClient, settings: Settings) -> None:
    result = json_object(auth_client.login(settings.username, settings.password))
    assert result["username"] == settings.username
    assert isinstance(result["id"], int) and result["id"] > 0
    assert isinstance(result.get("accessToken"), str) and bool(result["accessToken"])
    assert isinstance(result.get("refreshToken"), str) and bool(result["refreshToken"])


@pytest.mark.smoke
def test_authenticated_user(users_client: UsersClient, settings: Settings) -> None:
    result = json_object(users_client.me())
    assert result["username"] == settings.username
    assert isinstance(result["id"], int) and result["id"] > 0


@pytest.mark.regression
def test_refreshed_token_authenticates_same_user(
    token_manager: TokenManager, users_client: UsersClient
) -> None:
    before = json_object(users_client.me())
    token_manager.refresh()
    after = json_object(users_client.me())
    assert after["id"] == before["id"]
    assert after["username"] == before["username"]
    # JWTs issued within the same second may match; token inequality is not a requirement.
