# Test targets and responsibilities

| Folder | Purpose | Network |
| --- | --- | --- |
| `unit/` | Cache/config, schema fault injection, strict models, envelope/diagnostic policy | None |
| `local/` | HTTP failures, auth isolation, query encoding, refresh, log protection | Loopback only |
| `functional/` | Eleven e-commerce scenarios parameterized for local and live | Loopback or DummyJSON |
| `contracts/` | Typed product view and refresh response compatibility | Loopback or DummyJSON |
| `negative/` | Thirteen invalid request cases with expected statuses/error shape | Loopback or DummyJSON |
| `boundary/` | Six page/search/quantity cases with business relationships | Loopback or DummyJSON |
| `booker/` | Ten persistent lifecycle/auth/filter/boundary cases with isolated fixtures | Loopback or Booker |
| `reqres/` | Four demo and five project cases, separate targets/auth/CI | Loopback or ReqRes; project live needs your key |
| `support/` | Small per-service HTTP models and owned booking/record trackers | Random loopback ports |

The `settings` fixture generates `[local]` and `[live]` cases. `[live]` carries the
`external` marker and is skipped unless `--run-external` is present. Local HTTP uses
the actual Playwright driver; it does not replace `ApiClient.get` with a mock.

The server is rebuilt for each test. It uses deliberately different IDs from public
examples, which helps catch hidden fixed-ID assumptions. It implements only behavior
needed by this phase. Its responses are **not authoritative DummyJSON contracts**.
Local tests can pass even if the public service changes; run live checks to detect that.
Booker has its own `booker_settings` fixture so service targets do not form a
DummyJSON × Booker Cartesian product.
ReqRes likewise has separate demo/project settings; adding it does not multiply
the other services' target fixtures. A live project selection without configured
key/project fails in setup before HTTP; it is not silently skipped.

Fixture chain for an authenticated call:

1. `settings` selects the target.
2. `auth_context` and `api_context` create separate request contexts.
3. `auth_client` uses `auth_context` for login/refresh cookies.
4. `token_manager` gets tokens lazily on the first authenticated call.
5. `authenticated_api` injects the Bearer header for `users_client`.
6. Pytest disposes both contexts after that test, releasing response buffers/cookies.

All test-specific contexts, tokens, and payloads are function-scoped. The Playwright
driver is session-scoped. Tests do not depend on test order or another test's login.

Selection examples:

```bash
python -m pytest tests/functional/test_products.py -m "not external"
python -m pytest tests/functional/test_auth.py -m external --run-external
python -m pytest -m "regression and not external"
python -m pytest -m "booker and not external"
python -m pytest -m "booker and external" --run-external
python -m pytest -m "reqres and not external"
python -m pytest -m "reqres_demo and external" --run-external
python -m pytest -m "reqres_project and external" --run-external
python -m pytest --collect-only -q
```

Use `contract_json` before reading supported response fields. Assert relationships,
not complete response snapshots. For example, compare the returned cart's user ID
with the discovered user's ID; do not require a fixed catalogue count.

Each `[live]` cart-add case performs one documented simulated write. There is no
load loop, fuzzing, or broad security probing. Read [the strategy](../docs/testing-strategy.md)
before expanding external coverage.

For persistent Booker data, read [the Phase 3 guide](../docs/phase-3-walkthrough.md).
Keep the synthetic lastname marker unchanged during mutations. Never delete or
update shared seed IDs. Eight loopback failure-injection checks validate cleanup,
including early ID registration, ownership changes, failure continuation, and logs.

ReqRes project tests use only records created by that test, preserving the synthetic
name marker. Seventeen loopback checks cover cleanup (including negative-create
unexpected success), key isolation, safe path segments, redacted logs/errors, and
429/Retry-After without replay. Demo POST is simulated and needs no cleanup.
See [Phase 4](../docs/phase-4-test-plan.md) for account setup and verification limits.
