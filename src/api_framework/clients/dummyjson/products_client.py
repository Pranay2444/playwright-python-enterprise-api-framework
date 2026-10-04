from playwright.sync_api import APIResponse

from api_framework.core.api_client import ApiClient


class ProductsClient:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def list(self, *, limit: int = 10, skip: int = 0) -> APIResponse:
        return self.api.get("/products", params={"limit": limit, "skip": skip})

    def get(self, product_id: int) -> APIResponse:
        return self.api.get(f"/products/{product_id}")

    def search(self, query: str) -> APIResponse:
        return self.api.get("/products/search", params={"q": query})
