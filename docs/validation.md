# Validation records

## Phase 5 — 2026-10-04

Implemented version **0.5.0**, continuing the saved authentication-lab checkpoint
rather than rebuilding earlier phases. This final phase combines the owned app,
MFA/documents, bounded security/property tests, Docker integration and parallel
reporting. Read [workflow/layers](phase-5-workflow.md), [auth policy](phase-5-auth.md),
[execution walkthrough](phase-5-walkthrough.md), [test plan](phase-5-test-plan.md),
and [domain defects/RCA](defect-management.md).

### Local verification

| Check | Executed result |
| --- | --- |
| Full deterministic suite / JUnit | **289 passed; 52 deselected in 31.80 seconds** |
| Allocation | 152 unit + 36 local HTTP + 32 DummyJSON + 10 Booker + 9 ReqRes + 50 owned lab |
| Two-worker owned lab | **50 passed in 14.34 seconds**, SQLite/captured delivery |
| Focused reporting/concurrency/generated HTTP batch | **9 passed** before the final unexpected-failure case was added |
| Ruff lint / formatting | Passed |
| Wheel + sdist build | Passed |
| Installed-wheel probe outside src | Both packages, three public schema assets, actual HTTP health/register/auth rejection passed |
| Source archive contents | Compose/Docker/scripts/docs/schema assets present; no private keys, DBs or venv |
| Markdown local file targets | 175 checked; remote URLs and anchors excluded |
| Workflow/Compose/issue-form YAML | Parsed successfully; not a Docker execution substitute |
| Signing-key initializer | 0600 file/0700 directory, repeat invocation preserves value, git ignored; no key output |
| Diff whitespace | Passed |

Local execution used Linux/Python **3.12.14**, Pytest **9.1.1** and Playwright
**1.63.0**. Updated exact pins include FastAPI, SQLAlchemy, psycopg, Argon2/pwdlib,
PyJWT, PyOTP, multipart, Hypothesis and xdist in `requirements-dev.txt`; lab app
requirements remain an optional package extra. The 52 deselected cases are 51
public live versions plus one explicitly opted-in container workflow.

New coverage includes strict signature/claim/time checks, challenge/step/refresh
replay, per-account attempt limits, fail-closed client/server failure handling,
owner/tenant/member gates, persistence/checksum/deletion, uniqueness/CAS races,
consistent login/verify lock order, bounded generated cases, Mailpit correlation,
and safe reporting with original-failure preservation. Race tests are bounded
regressions, not a performance/exhaustive-concurrency proof.

### CI / real infrastructure execution

Initial source commit `e80a97d` was published without force. Its
[first push run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37218454842)
passed all three quality jobs: Python 3.11/3.12/3.13 each ran **284 deterministic
cases**, formatting/lint/build, installed-wheel HTTP/assets and docs checks.
Docker startup and app PID1 UID 10001 verification passed. The real PostgreSQL/SMTP
job reported **31 failed, 19 passed** due to the Mailpit reader assuming UUID message
IDs; container smoke was not executed. Artifact upload and disposable stack teardown
completed. This is a framework adapter failure, retained in
[the redacted RCA](defects/phase-5-mailpit-adapter.md).

Mailpit v1.31.4 source confirms 22-character base62 IDs. The corrected reader validates
that format and normalizes CRLF. New regressions also check wrong body correlation
and unsafe IDs. Focused reader/document checks: **27 passed**. A separate pre-fix
CRLF unit case failed; the first CI did not reach its message body, so its newline
format is not inferred. Final local suite is **289 passed**, recorded above.

Correction commit `30caa55` passed the
[real infrastructure retest](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37219082102).
The inspected job logs and artifacts establish these executed outcomes:

| Job / check | Actual outcome |
| --- | --- |
| Quality Python 3.11 | **289 passed; 52 deselected in 31.60 seconds** |
| Quality Python 3.12 | **289 passed; 52 deselected in 29.76 seconds** |
| Quality Python 3.13 | **289 passed; 52 deselected in 29.75 seconds** |
| Every quality job | Ruff, build, installed-wheel real HTTP/assets and 175 local doc file targets passed |
| Compose | Actual image build/start/readiness passed for PostgreSQL 17, Mailpit v1.31.4 and app |
| Application privilege | PID1 effective execution UID 10001 check passed |
| PostgreSQL + real SMTP/Mailpit | **50 passed in 18.48 seconds**, two xdist workers with isolated schemas |
| Installed app container | **1 passed in 0.77 seconds**; email MFA/document/checksum/delete/refresh/logout |
| Artifacts and cleanup | All four executed jobs uploaded JUnit artifacts; owned job stopped and removed its disposable volume successfully |

Artifact names: `local-results-3.11`, `local-results-3.12`, `local-results-3.13`,
`owned-lab-results`; configured retention is seven days. Failure receipts are
uploaded when failures exist. All four public live jobs were disabled on this push;
no new provider live outcome is implied. The source retest used Python 3.12.14 for
owned infrastructure. Local Docker/PostgreSQL were unavailable; the actual checks
above ran through GitHub Actions rather than a substitute model.

A subsequent documentation-only commit records this evidence and closes the RCA;
its push quality/owned gates validate the maintained repository state separately.
No Python source, dependency pin, or workflow is changed by that evidence commit.

### Limits retained

The five private ReqRes project live cases remain unexecuted without the user's
key/project configuration. Phase 4's **46 public live passes** remain historical
point-in-time evidence; no new provider live run is implied by the Phase 5 local
suite. No credentials, real SMS recipients, defect issues or messages are created.

This is an owned disposable auth/document lab. TOTP enrollment/storage is
simplified; SMS is simulated; files are bounded UTF-8 text in the DB. No production
identity guarantee, full OpenAPI verification, UI, malware scanner, distributed
rate limiter, migration/retention worker, exhaustive fuzzing or load SLA is claimed.
Receipts are allowlisted metadata; JUnit/custom assertions still need review before
sharing. Expired sessions/refresh history and synthetic container accounts remain
until disposable database reset. See the auth/workflow guides for exact semantics.

---

## Phase 4 — 2026-10-04

Implemented version **0.4.0**: ReqRes demo/project clients, per-request API-key
policy, explicit project/environment config, strict starter-product data, partial
response schemas, reviewed OpenAPI excerpt, owned-record cleanup, and independent
CI toggles. No new runtime/development dependency; Phase 2 pins remain unchanged.

### Local verification

| Check | Result |
| --- | --- |
| Editable 0.4.0 install | Passed |
| Lint / formatting | Passed |
| Deterministic suite with JUnit | **203 passed; 51 live cases deselected in 5.67 seconds** |
| Allocation | 116 unit + 36 local HTTP + 32 DummyJSON + 10 Booker + 9 ReqRes |
| New focused checks | **54 passed; 9 live versions deselected** |
| New ReqRes allocation | 28 unit + 17 local HTTP + 4 demo + 5 project |
| Collection | 254 cases, including 51 live versions |
| Distribution build / installed-wheel probe | All three service validators and sdist schema assets passed |
| Markdown file links / diff whitespace | Passed |

Executed on Linux with Python **3.12.14**, Pytest **9.1.1**, Playwright **1.63.0**,
jsonschema **4.26.0**, and Pydantic **2.13.5**. Tests cover API-key header/repr safety,
target/config policy, strict generated data, nested schema failures, anonymous
header isolation, cleanup after ordinary/schema failures and unexpected negative
create success, changed owners, continued cleanup, redacted errors, and four-method
429/Retry-After preservation without replay.

### CI and live evidence

Phase 4 source was published on `main` in commit `3b65d61`.

The [push quality run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37207578460)
passed on Python **3.11, 3.12, and 3.13**, including lint, formatting, distribution
builds, and **203 deterministic tests per matrix job**.

The [explicit live run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37207678688)
passed all three quality jobs and all three enabled live jobs on Python **3.12.14**:

| Job | Executed outcome |
| --- | --- |
| `live-dummyjson` | **32 passed; 222 deselected in 2.79 seconds** |
| `live-booker` | **10 passed; 244 deselected in 1.56 seconds** |
| `live-reqres-demo` | **4 passed; 250 deselected in 2.41 seconds** |
| `live-reqres-project` | **Disabled input; not executed** |

The **46 live passes** confirm existing DummyJSON/Booker compatibility and anonymous
ReqRes demo pagination, discovered-user detail, empty pages, and simulated POST
echoes at execution time. No teardown errors were reported. ReqRes project
persistence, project-key authentication, and cleanup remain local-model evidence
until the five configured project cases run against the user's collection.

All six executed jobs uploaded JUnit artifacts successfully, with seven-day
retention. Public execution used GitHub Actions. A later documentation-only commit
records these results and updates older service selectors; Python source, schemas,
dependency pins, and workflow configuration are unchanged by that commit.

### Account and provider limitations

No user-owned ReqRes key/project configuration is available in this session.
The five project live cases are **not executed**. To verify, add the REQRES_API_KEY
repository Secret and REQRES_PROJECT_ID Variable using the
[Phase 4 walkthrough](phase-4-walkthrough.md), then enable the project live toggle.
Selecting project live tests without config fails before HTTP; it is not a skip/pass.

The newer LLM/landing references describe keyless demo access, which the four
executed demo cases confirmed; older docs and OpenAPI declarations differ. The
guide mentions project PATCH but the reviewed
spec does not; only PUT is implemented. See [the plan](phase-4-test-plan.md) for
the dated source review and snapshot. Direct workspace retrieval of the spec/LLM
JSON/pricing.md encountered HTTP errors; official web retrieval supplied the
reviewed spec/reference. Machine-readable pricing was unavailable, so free quotas
are advertised source claims, not measured account entitlements.

No live quota exhaustion/enforcement, public-key RBAC, app-user sessions, full
OpenAPI conformance, database erasure, production guarantee, UI, MFA, or retry
scheduler is claimed. DELETE/GET 404 establishes default API absence; soft deletion
and quota reclamation require separate provider/account evidence. Cleanup cannot
be guaranteed after process termination, unusable IDs, ownership changes, or
auth/network failures; GET-then-DELETE is not atomic.

---

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
