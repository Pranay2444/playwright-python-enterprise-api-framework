import pytest

from api_framework.clients.dummyjson.carts_client import CartsClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.core.responses import json_object
from api_framework.data.cart_factory import cart_payload


@pytest.mark.regression
def test_get_user_by_authenticated_id(users_client: UsersClient) -> None:
    current = json_object(users_client.me())
    user = json_object(users_client.get(current["id"]))
    assert user["id"] == current["id"]
    assert user["username"] == current["username"]


@pytest.mark.regression
def test_get_existing_carts_for_discovered_user(carts_client: CartsClient) -> None:
    existing_carts = json_object(carts_client.list())["carts"]
    assert existing_carts, "The demo needs at least one existing cart for this scenario"
    user_id = existing_carts[0]["userId"]
    result = json_object(carts_client.for_user(user_id))
    assert result["carts"]
    assert all(cart["userId"] == user_id for cart in result["carts"])
    assert any(cart["id"] == existing_carts[0]["id"] for cart in result["carts"])


@pytest.mark.regression
def test_authenticated_user_cart_collection(
    users_client: UsersClient, carts_client: CartsClient
) -> None:
    user = json_object(users_client.me())
    result = json_object(carts_client.for_user(user["id"]))
    assert isinstance(result["carts"], list)
    assert all(cart["userId"] == user["id"] for cart in result["carts"])
    # An authenticated user can legitimately have no carts.


@pytest.mark.workflow
@pytest.mark.regression
def test_add_cart_from_discovered_user_and_product(
    users_client: UsersClient, products_client: ProductsClient, carts_client: CartsClient
) -> None:
    user = json_object(users_client.me())
    product = json_object(products_client.list(limit=1))["products"][0]
    payload = cart_payload(user["id"], product["id"], quantity=2)

    cart = json_object(carts_client.add(payload), expected_status=201)

    assert isinstance(cart["id"], int) and cart["id"] > 0
    assert cart["userId"] == user["id"]
    assert cart["totalProducts"] == 1
    assert cart["totalQuantity"] == 2
    assert len(cart["products"]) == 1
    assert cart["products"][0]["id"] == product["id"]
    assert cart["products"][0]["quantity"] == 2
    # No GET of the created ID: DummyJSON cart writes are simulated.
