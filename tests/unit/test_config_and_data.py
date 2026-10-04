from pathlib import Path

import pytest

from api_framework.config import Settings
from api_framework.data.cart_factory import cart_payload


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://example.com",
        "https://",
        "https://user:secret@example.com",
        "https://example.com/api",
        "https://example.com?q=secret",
        "https://example.com#fragment",
    ],
)
def test_reject_ambiguous_or_credential_bearing_origin(base_url: str) -> None:
    with pytest.raises(ValueError, match="HTTP"):
        Settings(base_url=base_url)


def test_environment_overrides_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in (
        "DUMMYJSON_BASE_URL",
        "DUMMYJSON_USERNAME",
        "DUMMYJSON_PASSWORD",
        "API_TIMEOUT_MS",
        "TOKEN_EXPIRES_IN_MINS",
    ):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("API_TIMEOUT_MS=1000\nDUMMYJSON_PASSWORD=temporary-secret\n")
    monkeypatch.setenv("API_TIMEOUT_MS", "2500")
    settings = Settings.from_env(env_file)
    assert settings.timeout_ms == 2500
    assert settings.password == "temporary-secret"
    assert "temporary-secret" not in repr(settings)
    # dotenv changes os.environ; restore the extra variable as well.
    monkeypatch.delenv("DUMMYJSON_PASSWORD")


def test_invalid_timeout_fails_before_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_TIMEOUT_MS", "0")
    with pytest.raises(ValueError, match="positive"):
        Settings.from_env()


def test_cart_payloads_do_not_share_mutable_data() -> None:
    first = cart_payload(503, 731)
    second = cart_payload(503, 731)
    first["products"][0]["quantity"] = 100
    assert second["products"][0]["quantity"] == 2


def test_cart_factory_rejects_invalid_quantity() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        cart_payload(503, 731, quantity=0)
