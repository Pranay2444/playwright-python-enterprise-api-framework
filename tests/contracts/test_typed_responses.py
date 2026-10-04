import pytest

from api_framework.clients.dummyjson.auth_client import AuthClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.config import Settings
from api_framework.contracts.models import Product
from api_framework.contracts.validation import contract_json

pytestmark = pytest.mark.contract


def test_discovered_product_parses_without_coercion(products_client: ProductsClient) -> None:
    page = contract_json(products_client.list(limit=1), "product_page")
    assert page["products"], "The demo catalogue must contain a product"
    discovered = Product.model_validate(page["products"][0])
    fetched = Product.model_validate(contract_json(products_client.get(discovered.id), "product"))
    assert fetched == discovered


def test_refresh_response_contract(auth_client: AuthClient, settings: Settings) -> None:
    login = contract_json(auth_client.login(settings.username, settings.password), "login")
    # Never compare or print the token values. Same-second JWTs may be identical.
    contract_json(auth_client.refresh(login["refreshToken"]), "tokens")
