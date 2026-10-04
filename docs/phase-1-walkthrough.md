# Phase 1: learn the code in small steps

This guide explains the Phase 1 foundation. Phase 2 is now implemented; continue
with [the Phase 2 walkthrough](phase-2-walkthrough.md) for contracts and negative tests.

## 1. Understand the minimum flow

A test calls a domain method such as `products_client.list()`. That method knows
`/products` and its query parameters. `ApiClient` sends the HTTP request through
Playwright. The test receives `APIResponse`, checks its status, parses JSON, and
asserts the business result.

Read these files in order:

1. `src/api_framework/config.py`
2. `src/api_framework/core/api_client.py`
3. `src/api_framework/clients/dummyjson/products_client.py`
4. `src/api_framework/core/responses.py`
5. `tests/functional/test_products.py`
6. `tests/conftest.py`
7. `src/api_framework/clients/dummyjson/auth_client.py`
8. `src/api_framework/auth/token_manager.py`
9. `tests/functional/test_users_and_carts.py`

## 2. Configuration

`Settings` is a frozen dataclass: once a test receives its settings, it cannot mutate
them accidentally. `from_env()` reads variables and optionally an explicitly named
`.env` file. Existing environment variables win over that file.

`timeout_ms` is measured in milliseconds because Playwright accepts milliseconds.
`token_expires_in_mins` is the lifetime requested from DummyJSON. The adapter converts
minutes to seconds for token scheduling. Username/password are excluded from the
dataclass representation to reduce accidental disclosure.

Practice: temporarily set `API_TIMEOUT_MS=0`. Run a live scenario and explain why
configuration should fail before an HTTP call. Restore the setting afterward.

## 3. The HTTP layer

`context.fetch()` is the generic Playwright request operation. We expose readable
`get()` and `post()` helpers for this phase. A Python dictionary passed as `data`
is serialized by Playwright as JSON; query values are passed through `params` so
the driver encodes them correctly.

The client returns an error response rather than raising just because it is 4xx/5xx.
That lets future negative tests assert the actual status. A network/TLS/timeout error
is different: there is no usable HTTP response, so we raise `ApiTransportError`.

Practice: run `python -m pytest tests/local/test_http_behavior.py::test_http_error_is_returned_once`.
Explain why a 503 response is returned once instead of automatically retried.

## 4. Pytest fixture injection

Look at `test_get_products(products_client)`. Pytest matches the parameter name to
the fixture named `products_client`. That fixture needs `api`, which needs
`api_context`, which needs `playwright` and `settings`. Pytest creates that dependency
chain automatically; the test does not call the fixture functions directly.

`yield context` provides the context to the test. The code after `yield` disposes it
when the test ends, including when an assertion fails. Context disposal releases
stored responses and cookies. The driver is reused for the session, but each test
has its own request context.

The parameterized `settings` fixture creates local/live versions of every functional
test. Local uses `LocalApi`; live loads the repository `.env`. The marker controls
network opt-in independently from fixture construction.

Practice: run `python -m pytest tests/functional/test_products.py --collect-only -q`.
Find the `[local]` and `[live]` versions before executing them.

## 5. Authentication and token caching

The first `users_client.me()` request asks `TokenManager` for a header. If no tokens
exist, the manager calls `AuthClient.obtain_tokens()`. It caches the token pair and
uses a monotonic clock to determine when to refresh. Repeated requests in the same
test reuse the token.

`TokenSource` is a protocol: it states the methods the manager needs without naming
DummyJSON. This is a small example of dependency inversion. A new service's adapter
can implement the same interface if its token lifecycle fits.

Login/refresh happen in a separate context because DummyJSON sets cookies too. This
keeps public requests from passing an auth test accidentally through a login cookie.
Tokens are never stored in a file or shared across tests.

Practice: read `test_refresh_at_margin_without_sleeping`. Trace the fake clock at
100, 369, and 370 seconds. Explain why the refresh happens at 370 and needs no sleep.

## 6. Dynamic chaining and factories

The cart workflow gets the current user, discovers a product, and passes their IDs
to `cart_payload()`. The factory returns a fresh dictionary. The test validates
the returned user/product/quantity relationships.

Practice: change the local product ID in `tests/support/local_api.py`. Run the local
functional suite. It should still pass because the tests extract IDs dynamically.
Revert the practice change before committing unless it adds useful coverage.

## 7. Your next small tasks

| Task | Learning goal | Completion check |
| --- | --- | --- |
| Run and explain one product test | HTTP client vs domain client vs assertions | Explain each layer without reading a script |
| Add a second quantity case with `pytest.mark.parametrize` | Test-data variation | Local cart workflow covers two positive quantities |
| Add a basic product schema in Phase 2 | Contract checks vs functional checks | Missing/wrong-type fields fail independently from business checks |
| Add invalid-login and missing-auth tests in Phase 2 | Negative behavior and fresh contexts | Expected failures are asserted, never hidden by retries |

For the quantity exercise, replace hardcoded expected quantities in the test with
the requested value. The local model already supports different quantities. Keep
the live case count modest.

## 8. GitHub workflow

Use a separate repository named `playwright-python-enterprise-api-framework` for
this project. Keep your earlier UI/API learning repository separate.

Once this project exists remotely:

```bash
git switch -c phase-2-contract-tests
# Make one focused change and run the checks.
git add src tests docs
git commit -m "Add product response contract checks"
git push -u origin phase-2-contract-tests
```

Review the diff before staging. Do not commit `.env`, `.venv`, generated reports, or
credentials. Open a pull request and describe the behavior plus validation evidence.
Avoid force pushes to `main`.

If the first repository creation must be done from your machine with GitHub CLI:

```bash
gh auth login
gh repo create Pranay2444/playwright-python-enterprise-api-framework --public --source=. --remote=origin --push
```

Use `--private` instead of `--public` if you want to review privately before making
the portfolio public. Do not run creation if that remote already exists; clone it.

## 9. Interview explanation

"I separated transport, service clients, authentication, and tests. Pytest fixtures
create isolated request contexts and inject clients. The token manager caches tokens
per test and refreshes proactively; it does not retry failed business requests. I
discover data dynamically and validate API relationships. Local HTTP checks give
repeatable feedback, while an explicitly enabled live suite checks DummyJSON."

Describe security/MFA/DB testing as the roadmap until you implement and
execute those phases. Be clear that cart creation here is simulated.
