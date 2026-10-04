# Phase 2 walkthrough

Phase 1 explained the request path and fixture lifecycle. Phase 2 makes compatibility
rules explicit and adds rejection/boundary coverage without moving assertions into
clients. Start with [Phase 1](phase-1-walkthrough.md) if the fixtures are unfamiliar.

## Recommended reading order

| Order | File | What to look for |
| --- | --- | --- |
| 1 | `core/responses.py` | Why status and media type precede parsing |
| 2 | `contracts/dummyjson.json` | Required fields, local references, shared pagination |
| 3 | `contracts/validation.py` | Resource loading, checked/cached validator, safe error construction |
| 4 | `contracts/models.py` | Strict types, selected product view, request aliases/constraints |
| 5 | `data/cart_factory.py` | Model validation followed by a fresh service payload |
| 6 | `tests/unit/test_contracts_and_models.py` | Deliberately broken fields and nested values |
| 7 | `tests/functional/test_products.py` | Schema first, business checks second |
| 8 | `tests/negative/test_rejected_requests.py` | Raw bad inputs, anonymous auth checks, explicit statuses |
| 9 | `tests/boundary/test_boundaries.py` | Discovered totals, empty results, quantity arithmetic |

All source paths above are under `src/api_framework/`; test paths start at the repo
root. Read [contracts.md](contracts.md) beside the code for the policy rationale.

## Follow one product request

```python
page = contract_json(products_client.list(limit=1), "product_page")
assert page["products"], "The catalogue must contain a product"
product = Product.model_validate(page["products"][0])
detail = contract_json(products_client.get(product.id), "product")
assert detail["id"] == product.id
```

The client chooses the endpoint. The transport sends HTTP. The envelope helper
checks status and JSON. JSON Schema checks the page and nested products. Pydantic
offers typed access to fields we consume. The last assertion verifies the resource
relationship; a schema alone cannot tell whether we fetched the requested product.

Extra response fields are compatible. Removing `price`, returning `stock: "8"`,
or nesting an invalid product fails. Pydantic's strict mode avoids disguising a
numeric string as a successful integer parse. Response models ignore unknown fields;
request models forbid them to catch generator typos before HTTP.

## Follow one negative auth request

The missing-token test receives `api`, which uses a fresh `api_context` with no
login cookies. It calls `/auth/me` directly and expects 401. It does not receive
`users_client`, because that fixture automatically obtains and injects a token.
The malformed-token variant sends a harmless invalid string on the same clean
context. These test service rejection, not cryptographic verification by our code.

For cart negatives, `users_client` discovers a valid user using the separate login
context; the cart client sends a raw malformed dictionary. Using `cart_payload`
would reject the bad input locally and never exercise the server.

## Boundary reasoning

`limit=0` means all products in DummyJSON; it is not an empty-page request.
`skip=total` is the first offset after the catalogue and should return an empty
array. The test discovers `total` rather than fixing a number from today's dataset.
The empty-search test uses a unique term instead of depending on a common word.

Cart quantities 1 and 3 establish the minimum valid generated quantity and a
multi-unit relationship. Tests compare money with `pytest.approx` for floating
arithmetic. They do not prescribe the provider's discount-rounding algorithm:
the returned discounted item/cart totals must agree and stay within the gross total.
DummyJSON writes remain simulated, so there is no read-after-write persistence claim.

## Run and inspect

```bash
python -m pytest -m "contract and not external"
python -m pytest -m "negative and not external"
python -m pytest -m "boundary and not external"
python -m pytest -m "boundary and external" --run-external
```

The last command contacts the real service. A loopback pass proves the framework
works with the model, while a live pass confirms current deployed behavior. Use
[validation.md](validation.md) for recorded execution rather than inferring live
coverage from test collection.

## Practice tasks

1. Add a missing `category` unit case; predict which rule fails before running it.
2. Add a valid zero-stock product case and explain why zero stock differs from zero ID.
3. Add a new optional product field and prove it does not break compatibility.
4. Remove a nested cart quantity in a unit payload; inspect the safe schema location.
5. Propose a server quantity-zero test. Check the upstream handler and explain why
   our factory rule is insufficient evidence for a server rejection expectation.

Never paste real tokens or enable `--showlocals` in shared runs. Use the defect triage
guide to distinguish the observation, expectation basis, hypothesis, and confirmed cause.

## Interview explanation

“I added partial JSON Schema contracts for response compatibility and strict
Pydantic models for typed product access and generated cart payloads. I kept
business assertions in tests, used fresh contexts for missing-auth cases, and
tested the validators with malformed nested data. The same API scenarios run
locally and against the public service; I report those results separately.”

Explain the limits too: no exhaustive specification, provider verification, RBAC,
JWT signature validation, real cart persistence, security audit, or load benchmark.
