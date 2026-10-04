# Source design

`api_framework` is an installed Python package under a standard `src/` layout.
Imports use `from api_framework...`; they do not depend on running from a special
folder or adding the source directory to `sys.path`.

| Layer | Knows about | Avoids |
| --- | --- | --- |
| Config | Origins, credentials, timeout, requested token lifetime | Making HTTP calls |
| Core | Playwright transport, metadata logging, basic JSON assertions | DummyJSON endpoint names |
| Auth | Token caching and refresh policy through `TokenSource` | Specific service URLs |
| Domain clients | Endpoints, query parameters, auth response fields | Pytest fixtures and test assertions |
| Data factories | Fresh payload structure | Shared mutable dictionaries |
| Contracts | Partial service schemas, strict typed views/inputs, safe diagnostics | HTTP calls, Pytest fixtures, business workflow assertions |

The DummyJSON `AuthClient` adapter parses tokens for `TokenManager`; its public
`login`, `me`, and `refresh` methods still expose raw responses for testing.
The `json_object` helper checks the HTTP/JSON envelope. `contract_json` builds on
it using a packaged Draft 2020-12 schema. Both return the original dict, so business
assertions remain visible in tests. See [contract maintenance](../docs/contracts.md).

To add a new endpoint:

1. Confirm its current official contract.
2. Add a short method to the appropriate service client.
3. Return `APIResponse`; keep business assertions in the test.
4. Use fixtures or earlier API calls to discover IDs.
5. Add the local test-double behavior needed to verify transport/wiring, then run
   the equivalent live scenario separately.
6. Update the test plan and clearly record which target was executed.

If the endpoint uses an existing shape, reuse its named contract. Otherwise add a
partial response definition, a malformed-response unit case, and a local/live case.
Keep typed models limited to fields callers consume; maintain overlapping product
constraints together. Schema assets are package data and must survive wheel builds.

To add another service later, create `clients/<service>/`, its configuration and
fixtures, and its real integration tests. Reuse `ApiClient`. Implement `TokenSource`
only if that service uses a compatible obtain/renew token lifecycle; do not pretend
an API key or cookie token has the same behavior without designing an adapter.

Phase 3 implements Booker PUT/PATCH/DELETE through `ApiClient.request`. Cookie
session headers stay in `clients/restful_booker/`, and no refresh is invented.
The contract registry selects checked-in files by an allowed service name; existing
DummyJSON calls keep their default. `json_array` supports filtered booking ID lists.
Test resource lifecycle/cleanup stays under `tests/support`, not in transport.

Phase 4 adds `clients/reqres`: anonymous demo users and explicit API-key project
records. `RecordsClient` wraps input in data, uses safe record paths, and sends the
key per request with project/env configuration. It reuses transport, without a
TokenSource or refresh fiction. `record_factory` validates starter product policy;
`reqres.json` validates partial response shapes. `RecordTracker` stays in test
support because cleanup is a test lifecycle concern. See the
[Phase 4 guide](../docs/phase-4-walkthrough.md) before changing project auth/data.

Richer auth providers and retry policies remain future work. Avoid speculative
wrapper methods with no users.
