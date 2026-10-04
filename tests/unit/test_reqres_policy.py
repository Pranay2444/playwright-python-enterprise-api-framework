from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from api_framework.clients.reqres.api_key import ApiKeyAuth
from api_framework.config import ReqResSettings
from api_framework.contracts.validation import ContractValidationError, validate_contract
from api_framework.data.record_factory import product_record_data


@pytest.mark.parametrize("key", ["", " key", "key ", "key\r\nX-Leak: value", "clé", "key\tvalue"])
def test_api_key_rejects_unsafe_values_without_echoing_them(key: str) -> None:
    with pytest.raises(ValueError, match="visible ASCII") as error:
        ApiKeyAuth(key)
    assert "X-Leak" not in str(error.value)


def test_key_and_settings_representations_hide_private_credentials() -> None:
    auth = ApiKeyAuth("private-api-key")
    settings = ReqResSettings(api_key="private-api-key", project_id="qa-project")
    assert "private-api-key" not in repr(auth)
    assert "private-api-key" not in repr(settings)
    headers = auth.headers()
    headers["x-api-key"] = "overwritten"
    assert auth.headers()["x-api-key"] == "private-api-key"


@pytest.mark.parametrize("values", [{}, {"api_key": "key"}, {"project_id": "project"}])
def test_project_configuration_requires_both_key_and_project(values: dict) -> None:
    with pytest.raises(ValueError, match="REQRES_API_KEY and REQRES_PROJECT_ID"):
        ReqResSettings(**values).require_project()


@pytest.mark.parametrize("slug", ["../products", "products?key=private", "products/x", ""])
def test_collection_slug_cannot_change_the_request_path(slug: str) -> None:
    with pytest.raises(ValueError, match="safe slug"):
        ReqResSettings(collection=slug)


def test_environment_requires_a_known_target() -> None:
    with pytest.raises(ValueError, match="prod or dev"):
        ReqResSettings(environment="unknown")


def test_environment_overrides_only_explicit_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    names = [
        "REQRES_BASE_URL",
        "REQRES_API_KEY",
        "REQRES_PROJECT_ID",
        "REQRES_COLLECTION",
        "REQRES_ENV",
        "API_TIMEOUT_MS",
    ]
    for name in names:
        monkeypatch.delenv(name, raising=False)
    file = tmp_path / ".env"
    file.write_text("REQRES_API_KEY=file-key\nREQRES_PROJECT_ID=file-project\n")
    monkeypatch.setenv("REQRES_API_KEY", "environment-key")
    settings = ReqResSettings.from_env(file)
    assert settings.api_key == "environment-key"
    assert settings.project_id == "file-project"
    monkeypatch.delenv("REQRES_PROJECT_ID")


def test_record_factory_produces_independent_markers_and_preserves_zero_false() -> None:
    first = product_record_data(price=0, in_stock=False)
    second = product_record_data(price=0, in_stock=False)
    assert first["name"] != second["name"]
    assert first["price"] == 0 and first["in_stock"] is False
    first["category"] = "Changed"
    assert second["category"] == "Portfolio"


@pytest.mark.parametrize("price", [-1, True, "9.99", float("nan"), float("inf")])
def test_factory_rejects_invalid_prices_without_coercion(price: Any) -> None:
    with pytest.raises(ValidationError):
        product_record_data(price=price)


def test_factory_rejects_string_stock_state() -> None:
    with pytest.raises(ValidationError):
        product_record_data(in_stock="false")


@pytest.mark.parametrize(
    "record",
    [
        {"id": True, "data": {}},
        {"id": "", "data": {}},
        {"id": "valid", "data": []},
        {"id": "valid"},
    ],
)
def test_contract_rejects_invalid_nested_record_envelopes(record: dict) -> None:
    with pytest.raises(ContractValidationError):
        validate_contract({"data": record}, "record_response", service="reqres")


def test_contract_accepts_additive_fields_and_redacts_invalid_values() -> None:
    validate_contract(
        {"data": {"id": "created", "data": {}, "extra": True}}, "record_response", service="reqres"
    )
    with pytest.raises(ContractValidationError) as error:
        validate_contract(
            {"data": {"id": "created", "data": "private-api-key"}},
            "record_response",
            service="reqres",
        )
    assert "private-api-key" not in str(error.value)
