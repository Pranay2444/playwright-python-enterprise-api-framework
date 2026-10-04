import pytest
from playwright.sync_api import APIResponse

from api_framework.clients.reqres.records_client import RecordsClient
from api_framework.config import ReqResSettings
from api_framework.contracts.validation import contract_json
from api_framework.core.api_client import ApiClient
from api_framework.data.record_factory import product_record_data
from tests.support.record_lifecycle import RecordTracker

pytestmark = [pytest.mark.reqres, pytest.mark.reqres_project]


def assert_record(response: APIResponse, record_id: str, expected: dict) -> None:
    record = contract_json(response, "record_response", service="reqres")["data"]
    assert record["id"] == record_id
    for field, value in expected.items():
        assert record["data"][field] == value


@pytest.mark.workflow
@pytest.mark.contract
def test_persistent_record_lifecycle(record_tracker: RecordTracker, records: RecordsClient) -> None:
    owned = record_tracker.create(product_record_data())
    assert_record(records.get(owned.record_id), owned.record_id, owned.data)
    replacement = {**owned.data, "price": 0, "in_stock": False, "category": "Updated"}
    assert_record(records.update(owned.record_id, replacement), owned.record_id, replacement)
    assert_record(records.get(owned.record_id), owned.record_id, replacement)
    deleted = records.delete(owned.record_id)
    assert deleted.status == 204
    assert deleted.body() == b""
    assert records.get(owned.record_id).status == 404


@pytest.mark.regression
@pytest.mark.contract
def test_search_finds_only_our_created_marker(
    record_tracker: RecordTracker, records: RecordsClient
) -> None:
    owned = record_tracker.create(product_record_data())
    page = contract_json(records.list(search=owned.data["name"]), "records", service="reqres")
    assert owned.record_id in [record["id"] for record in page["data"]]
    assert all(record["data"]["name"] == owned.data["name"] for record in page["data"])


@pytest.mark.negative
def test_missing_data_wrapper_is_rejected(
    reqres_project_api: ApiClient, records: RecordsClient, record_tracker: RecordTracker
) -> None:
    payload = product_record_data()
    response = reqres_project_api.request(
        "POST",
        records.path,
        params={"project_id": records.settings.project_id},
        headers={**records.auth.headers(), "X-Reqres-Env": records.settings.environment},
        data=payload,
    )
    record_tracker.remember_created_id(response, payload["name"])
    contract_json(response, "error", expected_status=400, service="reqres")


@pytest.mark.negative
@pytest.mark.parametrize("key", [None, "invalid-portfolio-key"])
def test_project_read_requires_a_valid_api_key(
    reqres_project_api: ApiClient, reqres_project_settings: ReqResSettings, key: str | None
) -> None:
    settings = reqres_project_settings
    headers = {"X-Reqres-Env": settings.environment}
    if key is not None:
        headers["x-api-key"] = key
    response = reqres_project_api.request(
        "GET",
        f"/api/collections/{settings.collection}/records",
        params={"project_id": settings.project_id, "search": "QA-invalid-auth", "limit": 1},
        headers=headers,
    )
    assert response.status == 401
