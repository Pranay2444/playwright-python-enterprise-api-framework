"""Validate a selected response against the owned app's published OpenAPI schema."""

from jsonschema import Draft202012Validator


class OpenApiResponseError(AssertionError):
    pass


def validate_openapi_response(spec: dict, path: str, method: str, status: int, body) -> None:
    try:
        schema = spec["paths"][path][method.lower()]["responses"][str(status)]["content"][
            "application/json"
        ]["schema"]
    except KeyError:
        raise OpenApiResponseError(
            "No declared JSON response contract for this operation/status"
        ) from None
    root = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "components": spec.get("components", {}),
        **schema,
    }
    if next(Draft202012Validator(root).iter_errors(body), None) is not None:
        # Do not attach jsonschema messages/instances, which may contain credentials.
        raise OpenApiResponseError("Response violates the declared OpenAPI JSON contract")
