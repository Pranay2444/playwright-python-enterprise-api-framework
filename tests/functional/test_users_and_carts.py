import pytest

from api_framework.clients.dummyjson.carts_client import CartsClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.contracts.validation import contract_json
from api_framework.data.cart_factory import cart_payload

pytestmark = pytest.mark.contract


@pytest.mark.regression
def test_get_user_by_authenticated_id(users_client: UsersClient) -> None:
    current = contract_json(users_client.me(), "user")
    user = contract_json(users_client.get(current["id"]), "user")
    assert user["id"] == current["id"]
    assert user["username"] == current["username"]


@pytest.mark.regression
def test_get_existing_carts_for_discovered_user(carts_client: CartsClient) -> None:
    existing_carts = contract_json(carts_client.list(), "cart_page")["carts"]
    assert existing_carts, "The demo needs at least one existing cart for this scenario"
    user_id = existing_carts[0]["userId"]
    result = contract_json(carts_client.for_user(user_id), "cart_page")
    assert result["carts"]
    assert all(cart["userId"] == user_id for cart in result["carts"])
    assert any(cart["id"] == existing_carts[0]["id"] for cart in result["carts"])


@pytest.mark.regression
def test_authenticated_user_cart_collection(
    users_client: UsersClient, carts_client: CartsClient
) -> None:
    user = contract_json(users_client.me(), "user")
    result = contract_json(carts_client.for_user(user["id"]), "cart_page")
    assert isinstance(result["carts"], list)
    assert all(cart["userId"] == user["id"] for cart in result["carts"])
    # An authenticated user can legitimately have no carts.


@pytest.mark.workflow
@pytest.mark.regression
def test_add_cart_from_discovered_user_and_product(
    users_client: UsersClient, products_client: ProductsClient, carts_client: CartsClient
) -> None:
    user = contract_json(users_client.me(), "user")
    product = contract_json(products_client.list(limit=1), "product_page")["products"][0]
    payload = cart_payload(user["id"], product["id"], quantity=2)

    cart = contract_json(carts_client.add(payload), "created_cart", expected_status=201)

    assert isinstance(cart["id"], int) and cart["id"] > 0
    assert cart["userId"] == user["id"]
    assert cart["totalProducts"] == 1
    assert cart["totalQuantity"] == 2
    assert len(cart["products"]) == 1
    assert cart["products"][0]["id"] == product["id"]
    assert cart["products"][0]["quantity"] == 2
    # No GET of the created ID: DummyJSON cart writes are simulated.
