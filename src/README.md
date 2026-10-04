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

`AuthClient` is the one adapter that parses tokens for `TokenManager`; its public
`login`, `me`, and `refresh` methods still expose raw responses for testing.
The `json_object` helper performs basic assertions, not a complete contract check.

To add a new endpoint:

1. Confirm its current official contract.
2. Add a short method to the appropriate DummyJSON client.
3. Return `APIResponse`; keep business assertions in the test.
4. Use fixtures or earlier API calls to discover IDs.
5. Add the local test-double behavior needed to verify transport/wiring, then run
   the equivalent live scenario separately.
6. Update the test plan and clearly record which target was executed.

To add another service later, create `clients/<service>/`, its configuration and
fixtures, and its real integration tests. Reuse `ApiClient`. Implement `TokenSource`
only if that service uses a compatible obtain/renew token lifecycle; do not pretend
an API key or cookie token has the same behavior without designing an adapter.

PUT/PATCH/DELETE, richer auth providers, and retry policies are intentionally future
work. `ApiClient.request(method, ...)` can already send another method if a real
Phase 2/3 test requires it. Avoid speculative wrapper methods with no users.
