from types import SimpleNamespace
from typing import Any

import pytest

from api_framework.core.responses import json_array, json_object


@pytest.mark.parametrize("media_type", ["application/json", "Application/JSON; charset=utf-8"])
def test_json_media_type_allows_parameters(media_type: str) -> None:
    response = SimpleNamespace(status=200, headers={"content-type": media_type}, json=lambda: {})
    assert json_object(response) == {}


@pytest.mark.parametrize(
    "media_type", ["", "text/html", "application/jsonp", "text/application/json"]
)
def test_json_media_type_rejects_misleading_substrings(media_type: str) -> None:
    response = SimpleNamespace(status=200, headers={"content-type": media_type}, json=lambda: {})
    with pytest.raises(AssertionError, match="application/json"):
        json_object(response)


@pytest.mark.parametrize("body", [[], None, "private-response-value"])
def test_non_object_response_is_rejected_without_body_dump(body: Any) -> None:
    response = SimpleNamespace(
        status=200, headers={"content-type": "application/json"}, json=lambda: body
    )
    with pytest.raises(AssertionError, match="Expected a JSON object") as error:
        json_object(response)
    assert "private-response-value" not in str(error.value)


def test_invalid_json_diagnostics_do_not_echo_body() -> None:
    def invalid_json() -> None:
        raise ValueError("private-malformed-response")

    response = SimpleNamespace(
        status=200, headers={"content-type": "application/json"}, json=invalid_json
    )
    with pytest.raises(AssertionError, match="valid JSON") as error:
        json_object(response)
    assert "private-malformed-response" not in str(error.value)


def test_json_array_accepts_collection_response() -> None:
    response = SimpleNamespace(
        status=200, headers={"content-type": "application/json"}, json=lambda: [{"bookingid": 601}]
    )
    assert json_array(response) == [{"bookingid": 601}]


@pytest.mark.parametrize("body", [{}, None, "private-response"])
def test_json_array_rejects_other_envelopes_without_echoing_values(body: Any) -> None:
    response = SimpleNamespace(
        status=200, headers={"content-type": "application/json"}, json=lambda: body
    )
    with pytest.raises(AssertionError, match="JSON array") as error:
        json_array(response)
    assert "private-response" not in str(error.value)
