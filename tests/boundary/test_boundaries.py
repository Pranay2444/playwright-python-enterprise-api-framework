from uuid import uuid4

import pytest

from api_framework.clients.dummyjson.carts_client import CartsClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.contracts.validation import contract_json
from api_framework.data.cart_factory import cart_payload

pytestmark = [pytest.mark.boundary, pytest.mark.contract, pytest.mark.regression]


def test_one_item_page_at_zero_offset(products_client: ProductsClient) -> None:
    page = contract_json(products_client.list(limit=1, skip=0), "product_page")
    assert len(page["products"]) == page["limit"] == 1
    assert page["skip"] == 0


def test_skip_at_catalogue_total_is_empty(products_client: ProductsClient) -> None:
    first = contract_json(products_client.list(limit=1), "product_page")
    page = contract_json(products_client.list(limit=1, skip=first["total"]), "product_page")
    assert page["products"] == []
    assert page["skip"] == first["total"]
    assert page["total"] == first["total"]
    assert page["limit"] == 0


def test_limit_zero_means_all_products(products_client: ProductsClient) -> None:
    # One catalogue call, not a load test. DummyJSON documents 0 as "all".
    page = contract_json(products_client.list(limit=0), "product_page")
    assert page["skip"] == 0
    assert len(page["products"]) == page["limit"] == page["total"]


def test_unmatched_search_is_valid_empty_page(products_client: ProductsClient) -> None:
    page = contract_json(
        products_client.search(f"portfolio-no-match-{uuid4().hex}"), "product_page"
    )
    assert page["products"] == []
    assert page["total"] == page["limit"] == 0


@pytest.mark.parametrize("quantity", [1, 3], ids=["minimum", "multiple"])
def test_cart_quantity_and_price_relationships(
    users_client: UsersClient,
    products_client: ProductsClient,
    carts_client: CartsClient,
    quantity: int,
) -> None:
    user = contract_json(users_client.me(), "user")
    page = contract_json(products_client.list(limit=1), "product_page")
    assert page["products"], "The demo catalogue must contain a product"
    product = page["products"][0]
    cart = contract_json(
        carts_client.add(cart_payload(user["id"], product["id"], quantity=quantity)),
        "created_cart",
        expected_status=201,
    )
    assert cart["userId"] == user["id"]
    assert cart["totalQuantity"] == quantity
    assert cart["totalProducts"] == len(cart["products"]) == 1
    item = cart["products"][0]
    assert item["id"] == product["id"]
    assert item["quantity"] == quantity
    assert item["price"] == product["price"]
    assert item["total"] == pytest.approx(product["price"] * quantity)
    assert cart["total"] == pytest.approx(item["total"])
    assert cart["discountedTotal"] == pytest.approx(item["discountedPrice"])
    assert 0 <= cart["discountedTotal"] <= cart["total"]
