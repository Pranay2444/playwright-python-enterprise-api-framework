from uuid import uuid4

import pytest

from api_framework.clients.reqres.demo_users_client import DemoUsersClient
from api_framework.contracts.validation import contract_json

pytestmark = [pytest.mark.reqres, pytest.mark.reqres_demo]


@pytest.mark.smoke
@pytest.mark.contract
def test_detail_matches_user_discovered_from_list(demo_users: DemoUsersClient) -> None:
    page = contract_json(demo_users.list(per_page=2), "demo_users", service="reqres")
    assert 0 < len(page["data"]) <= 2
    discovered = page["data"][0]
    detail = contract_json(demo_users.get(discovered["id"]), "demo_user_response", service="reqres")
    assert detail["data"] == discovered


@pytest.mark.boundary
def test_one_item_pages_are_disjoint(demo_users: DemoUsersClient) -> None:
    first = contract_json(demo_users.list(page=1, per_page=1), "demo_users", service="reqres")
    second = contract_json(demo_users.list(page=2, per_page=1), "demo_users", service="reqres")
    assert first["page"] == 1 and second["page"] == 2
    assert len(first["data"]) == len(second["data"]) == 1
    assert first["data"][0]["id"] != second["data"][0]["id"]


@pytest.mark.boundary
def test_page_after_reported_last_page_is_empty(demo_users: DemoUsersClient) -> None:
    first = contract_json(demo_users.list(), "demo_users", service="reqres")
    after = first["total_pages"] + 1
    empty = contract_json(demo_users.list(page=after), "demo_users", service="reqres")
    assert empty["page"] == after
    assert empty["data"] == []


@pytest.mark.regression
def test_create_echoes_synthetic_data_without_persistence_claim(
    demo_users: DemoUsersClient,
) -> None:
    payload = {"name": f"QA-{uuid4().hex}", "job": "Portfolio tester"}
    body = contract_json(
        demo_users.create(payload), "demo_created", expected_status=201, service="reqres"
    )
    assert body["name"] == payload["name"]
    assert body["job"] == payload["job"]
    # Demo writes echo data; no misleading read-after-write or cleanup call.
