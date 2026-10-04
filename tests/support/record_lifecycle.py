"""Cleanup only records created with this test's synthetic name marker."""

import re
from dataclasses import dataclass
from typing import Any, Self

from playwright.sync_api import APIResponse

from api_framework.clients.reqres.records_client import RecordsClient, safe_record_id
from api_framework.contracts.validation import contract_json
from api_framework.core.responses import json_object


class RecordCleanupError(AssertionError):
    """Cleanup could not confirm removal of owned project records."""


@dataclass(frozen=True)
class CreatedRecord:
    record_id: str
    data: dict[str, Any]


class RecordTracker:
    def __init__(self, records: RecordsClient) -> None:
        self.records = records
        self.pending: dict[str, str] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.cleanup()

    def create(self, data: dict[str, Any]) -> CreatedRecord:
        marker = data.get("name")
        if not isinstance(marker, str) or not re.fullmatch(r"QA-[0-9a-f]{32}", marker):
            raise ValueError("Tracked records require a unique QA- UUID name")
        response = self.records.create(data)
        record_id = self.remember_created_id(response, marker)
        if record_id is None:
            raise AssertionError(
                "Record creation returned no usable ID; cleanup cannot identify it"
            )
        contract_json(response, "record_response", expected_status=201, service="reqres")
        return CreatedRecord(record_id, data)

    def remember_created_id(self, response: APIResponse, marker: str) -> str | None:
        """Also track unexpected success from a negative create request."""
        if not re.fullmatch(r"QA-[0-9a-f]{32}", marker):
            raise ValueError("Tracked records require a unique QA- UUID name")
        try:
            body = response.json()
        except ValueError:
            return None
        record = body.get("data") if isinstance(body, dict) else None
        record_id = record.get("id") if isinstance(record, dict) else None
        if not safe_record_id(record_id):
            return None
        self.pending[record_id] = marker  # Before status, schema, or business checks.
        return record_id

    def cleanup(self) -> None:
        failures = []
        for record_id, marker in list(self.pending.items()):
            try:
                self._remove(record_id, marker)
            except Exception as error:
                detail = (
                    str(error) if isinstance(error, RecordCleanupError) else type(error).__name__
                )
                failures.append(f"Record {record_id}: {detail}")
            else:
                del self.pending[record_id]
        if failures:
            raise RecordCleanupError("Cleanup failed: " + "; ".join(failures))

    def _remove(self, record_id: str, marker: str) -> None:
        response = self.records.get(record_id)
        if response.status == 404:
            return
        if response.status != 200:
            raise RecordCleanupError(f"Ownership check returned HTTP {response.status}")
        # Metadata/schema drift must not block cleanup of a provably owned record.
        body = json_object(response)
        record = body.get("data")
        data = record.get("data") if isinstance(record, dict) else None
        if not isinstance(data, dict) or data.get("name") != marker:
            raise RecordCleanupError("Owner marker missing or changed; DELETE withheld")
        deleted = self.records.delete(record_id)
        if deleted.status not in {204, 404}:
            raise RecordCleanupError(f"DELETE returned HTTP {deleted.status}")
        absent = self.records.get(record_id)
        if absent.status != 404:
            raise RecordCleanupError(f"Removal check returned HTTP {absent.status}")
