from typing import Any

import pytest

from api_framework.clients.dummyjson.carts_client import CartsClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.config import Settings
from api_framework.contracts.validation import contract_json
from api_framework.core.api_client import ApiClient

pytestmark = [pytest.mark.negative, pytest.mark.regression]


@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_missing_login_field(api: ApiClient, settings: Settings, missing_field: str) -> None:
    payload = {"username": settings.username, "password": settings.password}
    del payload[missing_field]
    error = contract_json(api.post("/auth/login", data=payload), "error", expected_status=400)
    assert error["message"] == "Username and password required"


def test_invalid_credentials(api: ApiClient, settings: Settings) -> None:
    error = contract_json(
        api.post(
            "/auth/login", data={"username": settings.username, "password": "wrong-demo-password"}
        ),
        "error",
        expected_status=400,
    )
    assert error["message"] == "Invalid credentials"


@pytest.mark.parametrize("token", [None, "not-a-jwt"], ids=["missing", "malformed"])
def test_me_rejects_missing_or_malformed_token(api: ApiClient, token: str | None) -> None:
    # api_context has no login cookies. Do not use users_client or token_manager here.
    headers = {} if token is None else {"Authorization": f"Bearer {token}"}
    contract_json(api.request("GET", "/auth/me", headers=headers), "error", expected_status=401)


@pytest.mark.parametrize(
    ("payload", "status", "message"),
    [
        ({}, 401, "Refresh token required"),
        ({"refreshToken": "not-a-refresh-token"}, 403, "Invalid refresh token"),
    ],
    ids=["missing", "invalid"],
)
def test_refresh_rejects_bad_token(
    api: ApiClient, payload: dict[str, Any], status: int, message: str
) -> None:
    error = contract_json(api.post("/auth/refresh", data=payload), "error", expected_status=status)
    assert error["message"] == message


@pytest.mark.parametrize("product_id", ["0", "not-an-id"])
def test_product_id_not_found(api: ApiClient, product_id: str) -> None:
    # These identifiers cannot name a positive-integer resource; no catalogue guess.
    contract_json(api.get(f"/products/{product_id}"), "error", expected_status=404)


def test_unsupported_product_collection_method(api: ApiClient) -> None:
    # POST /products is not POST /products/add. DummyJSON returns 404, not 405.
    # An unmatched route may return HTML, so do not impose the API error schema.
    assert api.post("/products", data={}).status == 404


@pytest.mark.parametrize("products", [[], {}], ids=["empty-list", "wrong-type"])
def test_cart_rejects_invalid_product_collection(
    carts_client: CartsClient, users_client: UsersClient, products: Any
) -> None:
    user = contract_json(users_client.me(), "user")
    # Raw invalid payload intentionally bypasses the valid-data factory.
    contract_json(
        carts_client.add({"userId": user["id"], "products": products}), "error", expected_status=400
    )


def test_cart_requires_user(carts_client: CartsClient, products_client: ProductsClient) -> None:
    page = contract_json(products_client.list(limit=1), "product_page")
    assert page["products"], "The demo catalogue must contain a product"
    contract_json(
        carts_client.add({"products": [{"id": page["products"][0]["id"], "quantity": 1}]}),
        "error",
        expected_status=400,
    )
