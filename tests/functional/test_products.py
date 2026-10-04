import pytest

from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.core.responses import json_object


@pytest.mark.smoke
def test_get_products(products_client: ProductsClient) -> None:
    result = json_object(products_client.list(limit=5))
    assert isinstance(result["products"], list) and result["products"]
    assert 0 < len(result["products"]) <= 5
    assert result["total"] >= len(result["products"])
    for product in result["products"]:
        assert isinstance(product["id"], int) and product["id"] > 0
        assert isinstance(product["title"], str) and product["title"]
        assert isinstance(product["price"], (int, float)) and product["price"] >= 0


@pytest.mark.regression
def test_get_product_by_discovered_id(products_client: ProductsClient) -> None:
    discovered = json_object(products_client.list(limit=1))["products"][0]
    product = json_object(products_client.get(discovered["id"]))
    assert product["id"] == discovered["id"]
    assert product["title"] == discovered["title"]
    assert product["price"] == discovered["price"]


@pytest.mark.regression
def test_search_returns_discovered_product(products_client: ProductsClient) -> None:
    discovered = json_object(products_client.list(limit=1))["products"][0]
    result = json_object(products_client.search(discovered["title"]))
    assert any(product["id"] == discovered["id"] for product in result["products"])


@pytest.mark.regression
def test_pagination_returns_disjoint_pages(products_client: ProductsClient) -> None:
    first = json_object(products_client.list(limit=1, skip=0))
    second = json_object(products_client.list(limit=1, skip=1))
    assert first["products"], "The demo catalogue must contain at least two products"
    assert second["products"], "The demo catalogue must contain at least two products"
    assert first["skip"] == 0 and second["skip"] == 1
    assert first["products"][0]["id"] != second["products"][0]["id"]
