import json
from copy import deepcopy
from importlib.resources import files
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from api_framework.contracts.models import CartCreate, Product
from api_framework.contracts.validation import ContractValidationError, validate_contract
from api_framework.data.cart_factory import cart_payload

PRODUCT = {
    "id": 731,
    "title": "Demo Hammer",
    "price": 12.5,
    "category": "tools",
    "stock": 0,
    "rating": 4.3,
}


def test_packaged_schema_is_valid_and_accepts_additive_fields() -> None:
    schema = json.loads(files("api_framework.contracts").joinpath("dummyjson.json").read_text())
    Draft202012Validator.check_schema(schema)
    validate_contract({**PRODUCT, "newServiceField": {"any": "value"}}, "product")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", True),
        ("id", "731"),
        ("price", "12.5"),
        ("price", -1),
        ("stock", -1),
        ("rating", 5.1),
        ("title", ""),
        ("category", None),
    ],
)
def test_product_schema_rejects_incompatible_values(field: str, value: Any) -> None:
    with pytest.raises(ContractValidationError):
        validate_contract({**PRODUCT, field: value}, "product")


def test_missing_required_product_field() -> None:
    body = deepcopy(PRODUCT)
    del body["price"]
    with pytest.raises(ContractValidationError, match="required"):
        validate_contract(body, "product")


def test_nested_product_failure_is_detected() -> None:
    body = {"products": [{**PRODUCT, "stock": "0"}], "total": 1, "skip": 0, "limit": 1}
    with pytest.raises(ContractValidationError, match="items/properties/stock/type"):
        validate_contract(body, "product_page")


def test_nested_cart_quantity_failure_is_detected() -> None:
    item = {
        "id": 731,
        "title": "Demo Hammer",
        "price": 12.5,
        "quantity": "2",
        "total": 25,
        "discountPercentage": 10,
        "discountedTotal": 23,
    }
    body = {
        "id": 811,
        "userId": 503,
        "products": [item],
        "total": 25,
        "discountedTotal": 23,
        "totalProducts": 1,
        "totalQuantity": 2,
    }
    with pytest.raises(ContractValidationError, match="quantity/type"):
        validate_contract(body, "cart")


def test_schema_diagnostics_never_echo_token_values() -> None:
    secret = "private-token-must-not-appear"
    with pytest.raises(ContractValidationError) as error:
        validate_contract({"accessToken": {"secret": secret}, "refreshToken": secret}, "tokens")
    assert secret not in str(error.value)
    assert "accessToken/type" in str(error.value)


@pytest.mark.parametrize(
    ("contract", "field"), [("cart", "discountedTotal"), ("created_cart", "discountedPrice")]
)
def test_cart_contracts_preserve_endpoint_specific_discount_field(
    contract: str, field: str
) -> None:
    item = {
        "id": 731,
        "title": "Demo Hammer",
        "price": 12.5,
        "quantity": 2,
        "total": 25,
        "discountPercentage": 10,
        field: 23,
    }
    body = {
        "id": 811,
        "userId": 503,
        "products": [item],
        "total": 25,
        "discountedTotal": 23,
        "totalProducts": 1,
        "totalQuantity": 2,
    }
    validate_contract(body, contract)
    del item[field]
    other = "discountedPrice" if field == "discountedTotal" else "discountedTotal"
    item[other] = 23
    with pytest.raises(ContractValidationError, match="required"):
        validate_contract(body, contract)


def test_unknown_contract_is_a_configuration_error() -> None:
    with pytest.raises(ValueError, match="Unknown DummyJSON contract"):
        validate_contract(PRODUCT, "typo")


@pytest.mark.parametrize("quantity", [0, -1, True, "2", 2.5])
def test_generated_cart_rejects_invalid_quantity(quantity: Any) -> None:
    with pytest.raises(ValidationError):
        cart_payload(503, 731, quantity=quantity)


@pytest.mark.parametrize(("user_id", "product_id"), [(0, 731), (503, 0), (True, 731), (503, "731")])
def test_generated_cart_rejects_invalid_identifiers(user_id: Any, product_id: Any) -> None:
    with pytest.raises(ValidationError):
        cart_payload(user_id, product_id)


@pytest.mark.parametrize("products", [[], [{"id": 731, "quantity": 1, "unexpected": True}]])
def test_request_model_rejects_empty_items_or_unknown_fields(products: Any) -> None:
    with pytest.raises(ValidationError):
        CartCreate.model_validate({"userId": 503, "products": products})


@pytest.mark.parametrize(
    ("field", "value"),
    [("id", False), ("stock", "0"), ("price", "12.5"), ("price", float("inf")), ("rating", 6)],
)
def test_typed_product_does_not_hide_bad_service_values(field: str, value: Any) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({**PRODUCT, field: value})


def test_model_diagnostics_hide_invalid_inputs() -> None:
    secret = "private-input-must-not-appear"
    with pytest.raises(ValidationError) as error:
        CartCreate.model_validate({"userId": secret, "products": []})
    assert secret not in str(error.value)
