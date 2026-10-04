# Response contracts and strict models

Phases 2–4 separate three questions: did the endpoint return the expected HTTP
envelope, is the JSON structurally compatible, and does the result make business
sense? A response can pass its schema and still contain the wrong user's cart.

## Validation order

1. `json_object` checks status, the exact `application/json` media type (parameters
   such as `charset=utf-8` are allowed), valid JSON, and an object body.
2. `contract_json` runs a named JSON Schema Draft 2020-12 contract.
3. Tests assert identity, pagination, quantity, and monetary relationships.
4. Tests that need typed access use `Product.model_validate` after the schema check.

`POST /products` is deliberately a status-only check: an unmatched route may return
HTML. Do not force every error from every route into the JSON error contract.
Vendor `+json` media types are not accepted by this DummyJSON envelope helper;
add support only when an actual service contract requires it.

## Why two validation tools?

| Tool | Responsibility | Tradeoff |
| --- | --- | --- |
| JSON Schema | Explicit, reviewable response compatibility rules independent of Python | Needs deliberate maintenance as the service evolves |
| Pydantic | Strict typed product access and valid cart payload generation | Covers selected fields, not every returned property |
| Ordinary assertions | Relationships across fields and calls | Must stay readable and separate from shape checks |

The schemas and typed product view overlap on six product fields. Update both and
their negative unit cases together. We use a checked-in schema rather than generating
the entire API contract from Pydantic: server responses and our valid-input policy
have different responsibilities. This is not consumer-driven Pact testing, provider
verification, an exhaustive OpenAPI validator, or JWT signature verification.

## Named response contracts

`src/api_framework/contracts/dummyjson.json` contains local `$defs` references only.
Validators load assets through `importlib.resources`, check the schema, and cache one
validator per service/name. No schema is fetched from a network during a test.

| Name | Required fields/rules | Used by |
| --- | --- | --- |
| `product` | Positive integer id; nonempty title/category; price ≥ 0; stock integer ≥ 0; rating 0–5 | Detail and nested product pages |
| `product_page` | Product array plus total/skip/limit nonnegative integers | List, search, pagination boundaries |
| `user` | Positive id; nonempty username/firstName/lastName/email | Login identity, me, user detail |
| `tokens` | Nonempty accessToken and refreshToken strings | Refresh and login |
| `login` | User and token contracts together | Login response |
| `cart_item` | Identity, price, positive quantity, total, discount 0–100, discountedTotal | Existing cart items |
| `created_cart_item` | Same common fields, with discountedPrice | Simulated cart-add items |
| `cart` | Positive id/userId; existing-item array; nonnegative totals/counts | Existing carts |
| `created_cart` | Common cart fields with created-item contract | Simulated cart-add response |
| `cart_page` | Cart array plus total/skip/limit | Cart collections |
| `error` | Nonempty string message | Supported JSON rejection responses |

`pagination`, `cart_item_base`, and `cart_base` are shared definitions.
Existing cart items use `discountedTotal`; simulated additions use `discountedPrice`.
Their contracts deliberately enforce the endpoint-specific field. Arrays may be empty; a scenario that needs
data must assert that prerequisite. All response definitions allow extra fields.
We do not validate email syntax, thumbnails, every user attribute, complete JWT
contents, or a fixed catalogue snapshot. JSON Schema defines an integer mathematically
(e.g. JSON `1.0` can satisfy it); Pydantic's strict integer fields reject Python floats
and booleans. Numeric strings are rejected by both approaches.

## Request policy

`CartCreate` and `CartItem` require positive integer IDs and quantities, at least one
item, and no unknown fields. `cart_payload` validates these models and returns a
new dictionary using the service's `userId` alias. Pydantic rejects booleans and
numeric strings; `Product` also rejects nonfinite numbers. Negative server tests
send raw dictionaries deliberately, so the factory does not block the HTTP call.

DummyJSON's cart handler defaults/coerces some quantities and ignores some unknown
products. We do not assume it rejects quantity zero, negative values, or every
invalid item. Those stricter server validation checks belong in the owned app phase.

## Sources and confidence

The public docs establish normal flows and the `limit=0` behavior. Negative status
expectations were reviewed against the provider's source at commit
`3d78fed5f35b7f1087db1c162edc412f2a736722` on 2026-10-04:

- [Auth handlers](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/controllers/auth.js): missing/invalid credentials 400; missing refresh 401; invalid refresh 403.
- [Auth middleware](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/middleware/auth.js) and [error mapping](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/middleware/error.js): missing or malformed access token 401.
- [Resource helper](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/helpers/resource.js): nonexistent product 404; pagination limit reports returned length.
- [Product routes](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/routes/product.js): collection POST has no matching route; add is a separate path.
- [Cart handler](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/controllers/cart.js) and [user verification](https://github.com/Ovi/DummyJSON/blob/3d78fed5f35b7f1087db1c162edc412f2a736722/src/helpers/index.js): empty/non-array items and missing user 400.
- [Products documentation](https://dummyjson.com/docs/products), [auth](https://dummyjson.com/docs/auth), [carts](https://dummyjson.com/docs/carts).
- [jsonschema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/) and [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).

Provider source is evidence for an expectation, not proof that the deployed service
runs that revision. The live suite supplies the point-in-time compatibility signal;
see [validation](validation.md). Local server agreement only validates wiring.

## Safe failures and maintenance

`ContractValidationError` reports the contract name, failed rule, and schema path.
It omits `ValidationError.message`, `instance`, and response data because those can
contain tokens. Pydantic uses `hide_input_in_errors=True`. Raw Pydantic `.errors()`
can still contain inputs, and Pytest `--showlocals` can expose dictionaries. Never
share them unredacted. The tests inject private-looking values to verify displayed
diagnostics do not echo those values.

When a contract fails:

1. Reproduce the smallest local/live test and classify the failing layer.
2. Compare the safe location with provider documentation/source and project rules.
3. Confirm whether this is a service change, wrong expectation, bad data, or framework
   defect. An additive field alone should not fail.
4. Update only the supported rule; retain a malformed-response regression case.
5. Run the affected tests, full local gates, distribution build, and live verification.
6. Update this document, the plan, and executed validation evidence.

Schema files are included in wheel and source distributions. Package validation
must inspect the built assets and exercise a validator from an installed wheel;
an editable-install pass alone cannot detect missing package data.

## Phase 3 service extension

`restful_booker.json` adds token, auth-error, booking, created-booking, and booking-ID
array contracts. Pass `service="restful_booker"` to `contract_json` or
`validate_contract`; existing DummyJSON calls retain the default. Unknown service
names are rejected before file loading. Date patterns check ISO shape only; the
strict booking factory validates real dates and checkout ordering. `additionalneeds`
is optional in the response contract but asserted when our request includes it.

Use `json_array` plus `validate_contract` for the filtered ID array. Booker health,
403, deletion, and absence responses are status-only checks because their bodies
need not be JSON. Cleanup checks the JSON envelope and unique marker, independently
of unrelated full-booking schema drift. See [the Phase 3 plan](phase-3-test-plan.md).

## Phase 4: reviewed ReqRes contracts

Pass `service="reqres"` to select `reqres.json`. The partial definitions cover demo
user/list/detail/created responses and project record/list/error envelopes. Record
responses nest fields under `data.data`; IDs are strings. Additive fields remain
allowed. Dates/email formats are described in the provider excerpt but are not
enforced by our validator; don't claim full OpenAPI or format validation.

[The reviewed excerpt](reference/reqres-openapi-reviewed.json) records selected
OpenAPI 3.0.3 paths/schemas from API version 2.1.0, reviewed 2026-10-04. It is not
loaded at runtime. OpenAPI 3.0 schemas are not directly treated as Draft 2020-12;
our small response rules are maintained explicitly and exercised with malformed
nested unit inputs. Verify current docs/live behavior before extending the rules.

`ProductRecordData` enforces our starter Products generator policy: nonempty name
and category, finite/nonnegative price, strict boolean in_stock, and no extras.
The generic provider record data schema allows objects; a typed factory does not
prove every collection has those server validation rules. Negative wrapper tests
use raw requests and register unexpected successful creation IDs before asserting.
Cleanup checks marker ownership independently of unrelated metadata schema drift.
Read [the Phase 4 plan](phase-4-test-plan.md) for auth/PATCH documentation conflicts.
