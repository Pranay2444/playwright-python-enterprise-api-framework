# Troubleshooting

| Symptom | Check | Action |
| --- | --- | --- |
| `ModuleNotFoundError: api_framework` | Active interpreter and editable install | Activate `.venv`; run `python -m pip install --no-deps -e .` |
| Pytest command missing | Interpreter selection | Use `python -m pytest` after installing `requirements-dev.txt` |
| Live tests are skipped | `external` marker opt-in | Run `python -m pytest -m external --run-external` |
| All items are deselected | Marker expression or path | Use `python -m pytest --collect-only -q` to inspect node IDs |
| HTTP 403 or connection timeout on live API | Network/proxy vs actual API response | Compare with local tests; capture safe status details; do not disable TLS |
| Invalid origin/timeout configuration | `.env` and process environment | Fix the validation error; process environment wins over `.env` |
| Login expected 200 but returns another status | Credentials, public service health, current docs | Check published demo credentials; investigate before changing expectations |
| Cart ID cannot be fetched after add | DummyJSON simulated writes | Assert the add response; use a persistent service in a later phase |
| A user's carts are empty | Data assumption | An empty collection is valid; use discovered existing-cart owner for nonempty coverage |
| Refresh JWT matches the prior string | Token issuance timing | Validate authenticated identity; do not require different strings |
| VS Code cannot resolve imports | Selected Python interpreter | Select this project's `.venv` interpreter and reinstall editable package |
| `ContractValidationError` | Named contract, safe schema location, current provider response | Reproduce the smallest case; compare docs/contracts.md before changing rules |
| Pydantic rejects a numeric string or boolean | Strict request/view policy | Fix generated data; keep raw invalid dicts only in negative tests |
| Unknown contract name | Checked-in `$defs` names | Correct the name; this is configuration, not a product defect |
| Missing schema after wheel install | Package data and build artifact | Rebuild with contracts/*.json included; verify the installed resource |
| Booker create/delete status differs from REST assumptions | Provider-specific documented statuses | Assert create 200 and delete 201; verify using the Phase 3 plan |
| Booker writes return 403 | Cookie session, credentials, public/authenticated client | Use the Booker session for owned mutations; do not inject a DummyJSON Bearer token |
| Booking disappears during a live test | Shared demo reset or competing writes | Preserve failed evidence; check the target/time; do not hide with retries |
| Cleanup reports changed owner marker | ID reuse or a test changed lastname | Withhold deletion; inspect ownership and mutation code |
| Cleanup fails after a test passes/fails | Separate teardown outcome | Preserve both results; check safe GET/DELETE statuses; do not swallow errors |
| ReqRes project setup fails before HTTP | REQRES_API_KEY and REQRES_PROJECT_ID | Configure your QA manage key in ignored .env or GitHub Secret; project ID as a CI Variable |
| ReqRes project returns 400 | Data wrapper, collection schema, prod/dev target | Use data nesting and the correct starter/equivalent schema; verify the current plan |
| ReqRes demo returns 401/403 | Current demo-auth contract versus older docs, proxy/WAF evidence | Keep the failed result; no key guessing, TLS bypass, or automatic retry |
| ReqRes returns 429 | Request budget, concurrent callers, quota/Retry-After | Preserve the response and review account limits; no automatic replay or quota-exhaustion loops |
| ReqRes DELETE is 204 but JSON parsing fails | Empty successful response | Assert status and empty body, then separate GET 404 |
| ReqRes project PATCH expectation | Reviewed OpenAPI has PUT but no project PATCH | Use implemented PUT; verify an actual PATCH contract before extending the adapter |

Start a failure investigation with the smallest failing node:

```bash
python -m pytest 'tests/functional/test_auth.py::test_authenticated_user[local]'
python -m pytest 'tests/functional/test_auth.py::test_authenticated_user[live]' --run-external
```

Record local/live target, command, test ID, Python/dependency versions, timestamp,
and status. A proxy denial is not a proven product authorization defect. A local
pass with a live failure narrows the investigation; it does not prove the framework
is correct for every possible service response.

Do not use `--showlocals` on shared reports or paste raw Playwright transport logs
containing headers. The wrapper sanitizes transport errors; use a controlled manual
reproduction if more network evidence is required.
