# Validation records

## Phase 3 — 2026-10-04

Implemented version **0.3.0**: Restful Booker clients/settings/cookie session,
synthetic booking factory, service-specific schemas, persistent lifecycle scenarios,
and ownership-aware cleanup with loopback failure injection. Dependency pins remain
unchanged from Phase 2; no new runtime dependency is required.

### Local verification

| Check | Result |
| --- | --- |
| Editable 0.3.0 install | Passed |
| Lint and formatting | Passed |
| Deterministic suite with JUnit | **149 passed; 42 live cases deselected** |
| Allocation | 88 unit + 19 local HTTP framework/cleanup + 32 local DummyJSON + 10 local Booker |
| New cleanup regressions | 8 passed, including malformed persisted response and changed owner |
| Total collection | 191 cases |
| Distribution build and installed-wheel schemas | Passed for both services; both assets in sdist |
| Documentation file links / diff whitespace | Passed |

Executed on Linux with Python **3.12.14**, Pytest **9.1.1**, Playwright **1.63.0**,
jsonschema **4.26.0**, and Pydantic **2.13.5**. The Booker loopback target is a small
persistent model, not evidence of deployed service compatibility.

### CI and live evidence

Phase 3 source was published on `main` in commit `ece1927`.

The [push quality run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37204784710)
passed on Python **3.11, 3.12, and 3.13**, including lint, formatting, distribution
builds, and **149 deterministic tests per matrix job**.

The [explicit live run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37204906955)
passed all three quality jobs and both independent live jobs on Python **3.12.14**:

| Job | Executed outcome |
| --- | --- |
| `live-booker` | **10 passed; 181 deselected in 8.70 seconds** |
| `live-dummyjson` | **32 passed; 159 deselected in 5.98 seconds** |

Booker confirmed reviewed statuses, cookie-authenticated PUT/PATCH/DELETE, separate
GET persistence checks, exact-name filtering, zero/false PATCH values, and unchanged
bookings after rejected writes. Seven synthetic bookings were created; the lifecycle
case deleted its own booking and teardown verified absence for all tracked IDs.
No cleanup errors were reported. This is evidence at execution time, not permanent
durability or a guarantee against shared-demo resets.

DummyJSON's 32 existing live cases remained compatible with the shared response
and contract changes. All five JUnit artifacts were uploaded successfully, with
seven-day retention. Public execution used GitHub Actions; the local model remains
separate evidence.

A later documentation-only commit records these results without changing Python
source, schemas, dependency pins, or workflow configuration. Its push quality gate
validates the maintained repository state separately.

### Limits

Booker data persists within the shared demo dataset lifetime, which resets. Tests
use synthetic data and track returned IDs; teardown checks markers and GET 404.
GET-then-DELETE is not atomic. A changed marker, network/auth failure, unusable
creation ID, or process termination prevents guaranteed cleanup. Failures are
reported without retries or broad search/delete. No permanent durability, Basic-auth
coverage, production RBAC, database, MFA, UI, or performance claim is made.

---

## Phase 2 — 2026-10-04

Implemented version **0.2.0**: partial response schemas, strict Pydantic product/cart
models, negative API scenarios, boundary/arithmetic checks, and maintained strategy
and RCA instructions. The upstream existing-cart versus cart-add discount-field
difference is covered by distinct contracts and unit regressions.

### Local verification

| Check | Result |
| --- | --- |
| Exact dependency resolution and editable 0.2.0 install | Passed |
| `ruff check .` / `ruff format --check .` | Passed |
| Deterministic suite with JUnit XML | **102 passed; 32 live cases deselected** |
| Test allocation | 59 unit + 11 local HTTP framework + 32 local service cases |
| Collection including live versions | 134 cases |
| Wheel and source distribution build | Passed; schema asset included |
| Installed-wheel contract probe outside source package | Passed |
| Local Markdown file links and `git diff --check` | Passed |

Executed locally on Linux, Python **3.12.14**. New dependencies are jsonschema
**4.26.0** and Pydantic **2.13.5**; complete pins are in requirements-dev.txt.
The unit suite covers nested failures, additive fields, strict types, separate
existing/created cart discount fields, and value-free displayed diagnostics.

### GitHub Actions / live verification

Phase 2 source was published on `main` in commit `6335f0c`.

The [push quality run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37202412843)
passed on Python **3.11, 3.12, and 3.13**, including lint, formatting, distribution
builds, and **102 deterministic tests per matrix job**.

The [explicit live run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37202520073)
passed all three quality jobs and `live-dummyjson`. The live job used Python
**3.12.14** and reported **32 passed; 102 local cases deselected in 6.81 seconds**.
Its 32 cases include 11 baseline functional scenarios with schemas, 2 typed/refresh
contract scenarios, 13 negative cases, and 6 boundary/arithmetic cases. JUnit XML
artifacts were uploaded successfully; their configured retention is seven days.

This confirms the deployed service's reviewed statuses, both cart discount-field
shapes, and boundary semantics at execution time. It is not an uptime guarantee.
Public DummyJSON execution used GitHub Actions because this workspace previously
could not reach the service reliably. Local model passes remain separate evidence.

A later documentation-only commit records these results without changing Python
source, schema files, dependency pins, or workflow configuration. The final push
workflow validates that maintained repository state separately.

### Phase 2 limitations

Schemas describe only required fields consumed by the portfolio and allow additions.
They do not validate every field, email format, JWT signatures, or provider ownership.
Cart input models express our generator policy; the public API is more permissive.
Cart writes are simulated. There is no RBAC/security audit, load benchmark, database,
MFA, UI, or process-parallel execution claim.

---

## Phase 1 validation record

Validated on **2026-10-04** in a Linux workspace using Python **3.12.14**.
The local checks below were followed by successful GitHub Actions quality and live API runs.

## Executed checks

| Check | Command | Outcome |
| --- | --- | --- |
| Editable package install | `uv pip install --python .venv/bin/python -e '.[dev]'` | Passed |
| Dependency resolution | `uv pip compile pyproject.toml --extra dev -o requirements-dev.txt` | Passed; exact pins recorded |
| Lint | `ruff check .` | Passed |
| Formatting | `ruff format --check .` | Passed |
| Deterministic suite | `python -m pytest -m "not external" --junitxml=reports/local-results.xml` | **38 passed; 11 live cases deselected** |
| Distribution build | `python -m build` | Wheel and source distribution built successfully |
| One live probe | `python -m pytest 'tests/functional/test_products.py::test_get_products[live]' --run-external -q` | Failed before receiving HTTP response; see limitation below |

The 38 executed checks include 16 unit cases, 11 local HTTP framework cases, and
11 functional scenarios on the local target. The suite has 49 collected cases when
including the 11 opt-in live versions.

Validated dependency versions: Playwright **1.63.0**, Pytest **9.1.1**,
python-dotenv **1.2.4**, and Ruff **0.16.10**. Use `requirements-dev.txt` for all pins.

## GitHub Actions and live-service verification

The separate public repository was created and the complete source was published on `main`.
The first [quality run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37200416290)
passed on Python **3.11, 3.12, and 3.13**. Each quality job ran lint, formatting,
and the 38 deterministic cases.

The explicitly enabled [live verification run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37200593976)
also passed all three quality jobs and the `live-dummyjson` job. The live job ran
on Python 3.12 and reported **11 passed; 38 local cases deselected**, including
login, refresh, current-user identity, products/search/pagination, users/carts,
and simulated cart creation. JUnit results were uploaded as workflow artifacts.

These runs validate the Phase 1 source published in commit `3f9148a`.
The later documentation/workflow maintenance change keeps that Python source unchanged
and upgrades the official Actions to exact Node.js 24 release tags:
`checkout@v7.0.1`, `setup-python@v7.0.0`, and `upload-artifact@v7.0.1`.
The push workflow verifies the maintained configuration separately.

### Original workspace limitation

The live Playwright probe could not obtain an HTTP response from DummyJSON in this
workspace. A separate network attempt also encountered a forbidden response/timeout.
These are execution-environment observations, not confirmed DummyJSON product bugs.
The full live suite could not be run from this workspace, but subsequently passed
through GitHub Actions as recorded above. The original local transport failure is
retained here to distinguish environment reachability from service compatibility.

Run it from a machine with access or through the manually enabled CI live job:

```bash
python -m pytest -m external --run-external --junitxml=reports/live-results.xml
```

Do not change expected statuses or mark failures as passed to hide a network
limitation. The simulated cart-add `201` expectation was confirmed in the successful
live run.

## Other limits

- Local execution used Python 3.12; CI additionally verified Python 3.11 and 3.13.
- The live result is a point-in-time compatibility check, not an uptime guarantee.
- Local responses are a minimal test double, not verified full DummyJSON contracts.
- Phase 1 did not include JWT cryptographic validation, schema validation, security audit, load test, UI,
  database, MFA, persistent cart, or process-parallel execution.
