"""Status and JSON envelope assertions, without printing response bodies."""

from typing import Any

from playwright.sync_api import APIResponse


def json_object(response: APIResponse, expected_status: int = 200) -> dict[str, Any]:
    if response.status != expected_status:
        raise AssertionError(f"Expected HTTP {expected_status}; received HTTP {response.status}")
    content_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
    if content_type != "application/json":
        raise AssertionError("Expected an application/json response")
    try:
        body = response.json()
    except ValueError:
        raise AssertionError("Response did not contain valid JSON") from None
    if not isinstance(body, dict):
        raise AssertionError("Expected a JSON object")
    return body
