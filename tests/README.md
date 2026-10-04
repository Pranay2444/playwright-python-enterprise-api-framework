# Test targets and responsibilities

| Folder | Purpose | Network |
| --- | --- | --- |
| `unit/` | Cache/config, schema fault injection, strict models, envelope/diagnostic policy | None |
| `local/` | HTTP failures, auth isolation, query encoding, refresh, log protection | Loopback only |
| `functional/` | Eleven e-commerce scenarios parameterized for local and live | Loopback or DummyJSON |
| `contracts/` | Typed product view and refresh response compatibility | Loopback or DummyJSON |
| `negative/` | Thirteen invalid request cases with expected statuses/error shape | Loopback or DummyJSON |
| `boundary/` | Six page/search/quantity cases with business relationships | Loopback or DummyJSON |
| `support/` | A small in-process HTTP test double | Listens on a random loopback port |

The `settings` fixture generates `[local]` and `[live]` cases. `[live]` carries the
`external` marker and is skipped unless `--run-external` is present. Local HTTP uses
the actual Playwright driver; it does not replace `ApiClient.get` with a mock.

The server is rebuilt for each test. It uses deliberately different IDs from public
examples, which helps catch hidden fixed-ID assumptions. It implements only behavior
needed by this phase. Its responses are **not authoritative DummyJSON contracts**.
Local tests can pass even if the public service changes; run live checks to detect that.

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
python -m pytest --collect-only -q
```

Use `contract_json` before reading supported response fields. Assert relationships,
not complete response snapshots. For example, compare the returned cart's user ID
with the discovered user's ID; do not require a fixed catalogue count.

Each `[live]` cart-add case performs one documented simulated write. There is no
load loop, fuzzing, or broad security probing. Read [the strategy](../docs/testing-strategy.md)
before expanding external coverage.
