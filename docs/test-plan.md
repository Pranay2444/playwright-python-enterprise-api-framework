# DummyJSON functional test plan

Phase 1 scenarios remain the functional baseline. Phase 2 applies named response
contracts to these scenarios and adds the coverage in the
[Phase 2 test plan](phase-2-test-plan.md).

## Execution model

Run each functional scenario against the local HTTP target during development.
Run the same scenario against DummyJSON with
`-m "external and not booker and not reqres" --run-external` to verify the current
service. The local model validates composition; it is not a contract oracle.

P0 covers critical entry/identity behavior. P1 covers the e-commerce data flows.
The status expectations below must be checked on the live service before reporting
live compatibility. Cart creation's expected `201` is an explicit test expectation.

| ID | Priority | Test function | Expected outcome |
| --- | --- | --- | --- |
| AUTH-01 | P0 | `test_login_returns_tokens` | 200 JSON object; configured username; positive ID; string tokens |
| AUTH-02 | P0 | `test_authenticated_user` | 200; `/auth/me` resolves to configured username and valid ID |
| AUTH-03 | P0 | `test_refreshed_token_authenticates_same_user` | Refresh succeeds; next me request retains user ID/username |
| PROD-01 | P0 | `test_get_products` | 200; nonempty page bounded by requested limit; valid basic fields |
| PROD-02 | P1 | `test_get_product_by_discovered_id` | 200; discovered ID/title/price match detail response |
| PROD-03 | P1 | `test_search_returns_discovered_product` | 200; a discovered product appears in search results |
| PROD-04 | P1 | `test_pagination_returns_disjoint_pages` | 200; skip values honored; one-item pages contain different IDs |
| USER-01 | P1 | `test_get_user_by_authenticated_id` | 200; detail ID/username match authenticated user |
| CART-01 | P1 | `test_get_existing_carts_for_discovered_user` | 200; discovered existing cart is present and all owners match |
| CART-02 | P1 | `test_authenticated_user_cart_collection` | 200; collection is a list; any carts belong to authenticated user |
| CART-03 | P1 | `test_add_cart_from_discovered_user_and_product` | 201; simulated response has discovered owner/product and quantity 2 |

## Preconditions and assumptions

- The selected user's published credentials are valid.
- The catalogue has at least two products for pagination.
- At least one existing cart is available for CART-01.
- Empty carts are valid for CART-02; avoid vacuous coverage by retaining CART-01.
- Search by a discovered title should return that product. A live mismatch needs
  investigation of documented search semantics before changing the assertion.
- Cart additions are simulated; they require neither a read-after-write assertion
  nor a delete cleanup call.
- Public users/products/carts endpoints do not establish authorization rules.

## Framework checks

| Concern | Test location | Evidence |
| --- | --- | --- |
| Cache and expiry margin | `tests/unit/test_token_manager.py` | One login, margin-based refresh, failure invalidation, independent instances |
| Settings and factory | `tests/unit/test_config_and_data.py` | Origin checks, override precedence, positive values, independent payloads |
| Transport and diagnostics | `tests/local/test_http_behavior.py` | Status returned once, URL restriction, query encoding, log/error protection |
| Auth integration | `tests/local/test_http_behavior.py` | Separate contexts reject anonymous me; refresh reaches real HTTP route |

## Completion record

Record executed commands, result counts, runtime versions, and limitations in
[validation.md](validation.md). Link the CI run when one exists. Do not substitute
local test-double results for a live-service acceptance record.
