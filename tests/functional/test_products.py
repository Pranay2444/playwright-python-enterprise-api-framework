import pytest

from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.contracts.validation import contract_json

pytestmark = pytest.mark.contract


@pytest.mark.smoke
def test_get_products(products_client: ProductsClient) -> None:
    result = contract_json(products_client.list(limit=5), "product_page")
    assert isinstance(result["products"], list) and result["products"]
    assert 0 < len(result["products"]) <= 5
    assert result["total"] >= len(result["products"])
    for product in result["products"]:
        assert isinstance(product["id"], int) and product["id"] > 0
        assert isinstance(product["title"], str) and product["title"]
        assert isinstance(product["price"], (int, float)) and product["price"] >= 0


@pytest.mark.regression
def test_get_product_by_discovered_id(products_client: ProductsClient) -> None:
    discovered = contract_json(products_client.list(limit=1), "product_page")["products"][0]
    product = contract_json(products_client.get(discovered["id"]), "product")
    assert product["id"] == discovered["id"]
    assert product["title"] == discovered["title"]
    assert product["price"] == discovered["price"]


@pytest.mark.regression
def test_search_returns_discovered_product(products_client: ProductsClient) -> None:
    discovered = contract_json(products_client.list(limit=1), "product_page")["products"][0]
    result = contract_json(products_client.search(discovered["title"]), "product_page")
    assert any(product["id"] == discovered["id"] for product in result["products"])


@pytest.mark.regression
def test_pagination_returns_disjoint_pages(products_client: ProductsClient) -> None:
    first = contract_json(products_client.list(limit=1, skip=0), "product_page")
    second = contract_json(products_client.list(limit=1, skip=1), "product_page")
    assert first["products"], "The demo catalogue must contain at least two products"
    assert second["products"], "The demo catalogue must contain at least two products"
    assert first["skip"] == 0 and second["skip"] == 1
    assert first["products"][0]["id"] != second["products"][0]["id"]
