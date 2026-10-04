"""Validate structure separately from scenario-specific business assertions."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator
from playwright.sync_api import APIResponse

from api_framework.core.responses import json_object


class ContractValidationError(AssertionError):
    """A response violates a checked-in contract; diagnostics exclude values."""


_SCHEMAS = {
    "dummyjson": ("dummyjson.json", "DummyJSON"),
    "restful_booker": ("restful_booker.json", "Restful Booker"),
    "reqres": ("reqres.json", "ReqRes"),
}


@lru_cache(maxsize=32)
def _validator(contract: str, service: str) -> Draft202012Validator:
    if service not in _SCHEMAS:
        raise ValueError("Unknown contract service")
    filename, label = _SCHEMAS[service]
    schema = json.loads(files("api_framework.contracts").joinpath(filename).read_text())
    if contract not in schema["$defs"]:
        raise ValueError(f"Unknown {label} contract")
    schema["$ref"] = f"#/$defs/{contract}"
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_contract(body: Any, contract: str, *, service: str = "dummyjson") -> None:
    """Allow additive fields; reject missing required fields and incompatible types.

    Only schema locations and rule names appear in errors. jsonschema's default
    message can include the failing value, including a token, so we do not use it.
    """
    for error in _validator(contract, service).iter_errors(body):
        schema_path = "/".join(str(part) for part in error.absolute_schema_path)
        raise ContractValidationError(
            f"Contract '{service}/{contract}' failed rule '{error.validator}' "
            f"at schema /{schema_path}"
        ) from None


def contract_json(
    response: APIResponse, contract: str, *, expected_status: int = 200, service: str = "dummyjson"
) -> dict[str, Any]:
    body = json_object(response, expected_status)
    validate_contract(body, contract, service=service)
    return body
