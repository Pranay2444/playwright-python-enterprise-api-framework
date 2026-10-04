from collections.abc import Iterator

import pytest
from playwright.sync_api import Playwright

from api_framework.clients.reqres.records_client import RecordsClient
from api_framework.config import ReqResSettings
from api_framework.contracts.validation import ContractValidationError
from api_framework.core.api_client import ApiClient
from api_framework.data.record_factory import product_record_data
from tests.conftest import create_context
from tests.reqres.test_project_records import (
    test_missing_data_wrapper_is_rejected as reject_wrapper,
)
from tests.support.local_reqres import LocalReqRes
from tests.support.record_lifecycle import RecordCleanupError, RecordTracker


@pytest.fixture
def local_records(playwright: Playwright, local_reqres: LocalReqRes) -> Iterator[RecordsClient]:
    settings = ReqResSettings(
        base_url=local_reqres.base_url, api_key="local-manage-key", project_id="local-project"
    )
    context = create_context(playwright, settings)
    try:
        yield RecordsClient(ApiClient(context), settings)
    finally:
        context.dispose()


def test_cleanup_runs_after_a_business_failure(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    with pytest.raises(AssertionError, match="Synthetic assertion"):
        with RecordTracker(local_records) as tracker:
            tracker.create(product_record_data())
            raise AssertionError("Synthetic assertion")
    assert tracker.pending == {} and local_reqres.records == {}


def test_unrelated_metadata_contract_failure_does_not_prevent_cleanup(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    local_reqres.invalid_created_metadata = True
    with pytest.raises(ContractValidationError):
        with RecordTracker(local_records) as tracker:
            tracker.create(product_record_data())
    assert tracker.pending == {} and local_reqres.records == {}


def test_negative_create_unexpected_success_is_still_cleaned_up(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    local_reqres.accept_unwrapped_create = True
    with pytest.raises(AssertionError, match="Expected HTTP 400"):
        with RecordTracker(local_records) as tracker:
            reject_wrapper(local_records.api, local_records, tracker)
    assert tracker.pending == {} and local_reqres.records == {}


def test_changed_owner_blocks_deletion(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    tracker = RecordTracker(local_records)
    owned = tracker.create(product_record_data())
    local_reqres.records[owned.record_id]["data"]["name"] = "Another owner"
    with pytest.raises(RecordCleanupError, match="DELETE withheld"):
        tracker.cleanup()
    assert ("DELETE", f"{local_records.path}/{owned.record_id}") not in local_reqres.requests


def test_failed_delete_is_not_replayed_and_other_ids_are_cleaned(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    tracker = RecordTracker(local_records)
    first = tracker.create(product_record_data())
    second = tracker.create(product_record_data())
    path = f"{local_records.path}/{first.record_id}"
    local_reqres.forced_status[("DELETE", path)] = 429
    with pytest.raises(RecordCleanupError, match="HTTP 429"):
        tracker.cleanup()
    assert local_reqres.requests.count(("DELETE", path)) == 1
    assert first.record_id in tracker.pending
    assert second.record_id not in local_reqres.records


def test_already_deleted_and_repeated_cleanup_send_no_more_deletes(
    local_records: RecordsClient, local_reqres: LocalReqRes
) -> None:
    tracker = RecordTracker(local_records)
    owned = tracker.create(product_record_data())
    local_records.delete(owned.record_id)
    tracker.cleanup()
    events = list(local_reqres.requests)
    tracker.cleanup()
    assert local_reqres.requests == events
    assert local_reqres.requests.count(("DELETE", f"{local_records.path}/{owned.record_id}")) == 1


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_rate_limit_response_preserves_retry_after_without_replay(
    local_records: RecordsClient, local_reqres: LocalReqRes, method: str
) -> None:
    path = local_records.path
    local_reqres.forced_status[(method, path)] = 429
    response = local_records.api.request(
        method, path, data={"data": product_record_data()}, headers=local_records.auth.headers()
    )
    assert response.status == 429
    assert response.headers["retry-after"] == "30"
    assert local_reqres.requests == [(method, path)]


@pytest.mark.parametrize("record_id", ["../other", "id?key=private", "id/path", "", "id#fragment"])
def test_unsafe_record_id_fails_before_http(
    local_records: RecordsClient, local_reqres: LocalReqRes, record_id: str
) -> None:
    with pytest.raises(ValueError, match="safe nonempty"):
        local_records.delete(record_id)
    assert local_reqres.requests == []


def test_auth_is_per_request_and_absent_from_logs(
    local_records: RecordsClient, caplog: pytest.LogCaptureFixture
) -> None:
    with RecordTracker(local_records) as tracker:
        tracker.create(product_record_data())
        # Same context, raw API request: no inherited API-key header.
        response = local_records.api.get(local_records.path, params={"project_id": "local-project"})
        assert response.status == 401
    assert "local-manage-key" not in caplog.text
    assert "local-project" not in caplog.text


def test_arbitrary_cleanup_exception_values_are_redacted(
    local_records: RecordsClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracker = RecordTracker(local_records)
    tracker.create(product_record_data())

    def fail(record_id: str) -> None:
        raise RuntimeError("private-api-key")

    monkeypatch.setattr(local_records, "get", fail)
    with pytest.raises(RecordCleanupError) as error:
        tracker.cleanup()
    assert "private-api-key" not in str(error.value)
