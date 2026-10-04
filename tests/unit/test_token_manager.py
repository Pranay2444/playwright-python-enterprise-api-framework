import pytest

from api_framework.auth.token_manager import TokenManager, TokenPair


class DemoTokenSource:
    def __init__(self) -> None:
        self.login_count = 0
        self.refresh_count = 0
        self.fail_refresh = False

    def obtain_tokens(self) -> TokenPair:
        self.login_count += 1
        return TokenPair(f"access-{self.login_count}", "refresh", 300)

    def renew_tokens(self, refresh_token: str) -> TokenPair:
        assert refresh_token == "refresh"
        self.refresh_count += 1
        if self.fail_refresh:
            raise RuntimeError("Refresh unavailable")
        return TokenPair("renewed-access", "rotated-refresh", 300)


def test_multiple_reads_share_one_login() -> None:
    source = DemoTokenSource()
    manager = TokenManager(source)
    assert manager.access_token() == manager.access_token()
    assert manager.authorization_header() == "Bearer access-1"
    assert source.login_count == 1


def test_refresh_at_margin_without_sleeping() -> None:
    now = [100.0]
    source = DemoTokenSource()
    manager = TokenManager(source, clock=lambda: now[0])
    assert manager.access_token() == "access-1"
    now[0] = 369.0
    assert manager.access_token() == "access-1"
    now[0] = 370.0
    assert manager.access_token() == "renewed-access"
    assert source.login_count == 1
    assert source.refresh_count == 1


def test_invalidate_requires_new_login() -> None:
    source = DemoTokenSource()
    manager = TokenManager(source)
    manager.access_token()
    manager.invalidate()
    assert manager.access_token() == "access-2"


def test_refresh_failure_discards_stale_token() -> None:
    source = DemoTokenSource()
    manager = TokenManager(source)
    manager.access_token()
    source.fail_refresh = True
    with pytest.raises(RuntimeError, match="Refresh unavailable"):
        manager.refresh()
    assert manager.access_token() == "access-2"


def test_managers_do_not_share_credentials() -> None:
    first_source = DemoTokenSource()
    second_source = DemoTokenSource()
    first = TokenManager(first_source)
    second = TokenManager(second_source)
    first.access_token()
    second.access_token()
    first.invalidate()
    first.access_token()
    assert first_source.login_count == 2
    assert second_source.login_count == 1


def test_token_pair_repr_omits_secrets() -> None:
    tokens = TokenPair("secret-access", "secret-refresh", 300)
    assert "secret" not in repr(tokens)
