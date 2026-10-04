# Phase 2 risk-based test plan

The baseline [functional plan](test-plan.md) still applies; its eleven scenarios
now validate response contracts. Phase 2 adds 21 service scenarios, for 32 cases
per target including parameterization. Each uses the same client code against
loopback or live DummyJSON. Expected HTTP statuses are grounded in
[the contract basis](contracts.md), then confirmed by the live run.

## Service scenarios

| ID / priority | Risk and test | Data/precondition | Expected outcome | Marker |
| --- | --- | --- | --- | --- |
| CON-01 / P1 | `test_discovered_product_parses_without_coercion`: response types hidden by coercion | Discover one product | 200 page/detail; strict typed views agree | contract |
| CON-02 / P0 | `test_refresh_response_contract`: refresh shape changes | Valid configured demo login | 200 login + refresh; nonempty token strings | contract |
| NEG-01 / P0 | `test_missing_login_field` (2): incomplete login accepted | Omit username or password | 400; required-credentials message | negative |
| NEG-02 / P0 | `test_invalid_credentials`: wrong password accepted | Configured username, wrong demo password | 400; invalid credentials | negative |
| NEG-03 / P0 | `test_me_rejects_missing_or_malformed_token` (2): cookies hide auth rejection | Fresh API context, no token or malformed token | 401 JSON error | negative |
| NEG-04 / P0 | `test_refresh_rejects_bad_token` (2): refresh misuse accepted | Fresh context, absent or invalid refresh token | 401 missing; 403 invalid; JSON message | negative |
| NEG-05 / P1 | `test_product_id_not_found` (2): invalid identifier returns data | Zero or nonnumeric ID, independent of catalogue | 404 JSON error | negative |
| NEG-06 / P1 | `test_unsupported_product_collection_method`: wrong method silently accepted | POST collection path with empty body | 404; body format intentionally unspecified | negative |
| NEG-07 / P1 | `test_cart_rejects_invalid_product_collection` (2): malformed collection accepted | Authenticated discovered user; raw empty list/object | 400 JSON error | negative |
| NEG-08 / P1 | `test_cart_requires_user`: owner omitted | Discover product; raw payload without userId | 400 JSON error | negative |
| BND-01 / P1 | `test_one_item_page_at_zero_offset`: minimum page ignored | Catalogue has one or more products | 200; one item, skip 0 | boundary, contract |
| BND-02 / P1 | `test_skip_at_catalogue_total_is_empty`: end-of-data wrong | Discover total first; catalogue stable during test | 200; empty items, limit 0, same total/skip | boundary, contract |
| BND-03 / P1 | `test_limit_zero_means_all_products`: special limit misinterpreted | One bounded catalogue request | 200; item count = total = returned limit | boundary, contract |
| BND-04 / P1 | `test_unmatched_search_is_valid_empty_page`: empty shape broken | Unique UUID search term | 200; empty list, total/limit 0 | boundary, contract |
| BND-05 / P1 | `test_cart_quantity_and_price_relationships` (2): arithmetic/count mismatch | Discover user/product; quantities 1 and 3 | 201; correct identity/counts and price × quantity totals | boundary, contract |

Negative and boundary scenarios also carry `regression`. All `[live]` versions
carry `external` through the fixture. Exact message checks are limited to reviewed
authentication messages; schema checks do not dump the body on failure.

## Framework unit risks

| Concern | Check | Layer |
| --- | --- | --- |
| Response field removal or wrong type | Missing required price; booleans/numeric strings; negative/range values | Unit schema fault injection |
| Nested validation silently absent | Wrong product stock inside page; wrong quantity inside cart | Unit schema fault injection |
| Additive provider changes break tests | Accept an unknown response field; avoid full snapshots | Unit schema acceptance |
| Diagnostics expose secrets | Invalid token-shaped schema value and invalid model input omitted from displayed errors | Unit redaction |
| Factory coerces bad inputs | Reject zero/negative/boolean/string/fractional quantities and invalid IDs | Unit strict model |
| Invalid request shape generated | Reject empty items and unknown item properties | Unit strict model |
| Bad typed view silently accepted | Reject string/boolean fields, infinite price, out-of-range rating | Unit typed view |
| JSON substring accepted as media type | Accept parameters/case; reject JSONP, HTML, misleading prefix | Unit envelope |
| Package loses schema assets | Wheel/source build and installed-wheel validator probe | Packaging |

## Environment, data, and cleanup

Local fixtures rebuild the small server for every test. Real contexts are disposed
in teardown. Authentication-negative tests use the `api` fixture, never an
authenticated client or a context that already logged in. Valid users/products are
discovered at runtime; invalid IDs are impossible positive-integer resources rather
than guessed catalogue gaps. No cart cleanup is needed because writes are simulated.

There are three small simulated cart-add cases across both phases per target.
No repeated mutation loop, brute force, load test, exhaustive fuzzing, expiry sleep,
or cross-user access probing is included. Public endpoints do not prove RBAC.

## Acceptance and execution

```bash
python -m pytest tests/unit/test_contracts_and_models.py tests/unit/test_response_envelope.py
python -m pytest -m "negative and not external"
python -m pytest -m "boundary and not external"
ruff check .
ruff format --check .
python -m pytest -m "not external" --junitxml=reports/local-results.xml
python -m build
python -m pytest -m "external and not booker and not reqres" --run-external --junitxml=reports/live-results.xml
```

Completion requires distinguishable envelope/schema/model/business failures,
successful deterministic gates, packaged schema assets, documented limitations,
and honestly recorded live results. Counts, versions, and CI evidence belong in
[validation.md](validation.md), not in assumptions about service availability.
