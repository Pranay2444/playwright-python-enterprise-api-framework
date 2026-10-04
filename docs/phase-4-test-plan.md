# Phase 4: ReqRes API keys and project records

## Goal and current boundary

Add a third service through the existing Playwright transport. Keep public demo
fixture tests separate from project-scoped persistent CRUD. Use a per-request API
key, explicit project/environment configuration, partial response contracts, fresh
synthetic product records, and visible cleanup.

The implementation can run completely on loopback without any account. Live demo
and live project results are separate signals. Project live compatibility remains
pending until a user-owned manage key and project ID are configured and executed.
See [validation](validation.md) for actual outcomes; local passes are not live proof.

## Provider review — 2026-10-04

Reviewed primary sources:

- [Current LLM reference](https://reqres.in/llm.txt), labelled v2026-09-28.
- [Surface/auth overview](https://reqres.in/llms.txt).
- [OpenAPI](https://reqres.in/openapi.json), API version 2.1.0 / OpenAPI 3.0.3.
- [Docs](https://reqres.in/docs) and [QA guide](https://reqres.in/blog/qa-automation-with-reqres).
- [Landing page](https://reqres.in/) and advertised free-project limits.

[The reviewed OpenAPI excerpt](reference/reqres-openapi-reviewed.json) retains the
four paths and response/input schemas used here. It is a review snapshot, not a
complete provider spec, generated client, or runtime network dependency.

| Concern | Evidence / implementation decision |
| --- | --- |
| Demo access | Current landing/LLM references describe anonymous demo access; older docs and OpenAPI security declarations still say all `/api/*` need a key. Run keyless demo separately and retain live failures; never invent a valid key. |
| Demo writes | `/api/users` POST returns an echoed body, string ID, and createdAt; it is not persisted. No CRUD persistence or cleanup claim. |
| Project auth | `x-api-key`; manage key for server-side writes, public key for reads. This phase uses a user-owned manage key and does not claim public-key permission coverage. |
| Project target | Explicit `project_id` query plus `X-Reqres-Env` prod/dev; keys are never placed in a URL. Use a dedicated QA project/collection. |
| Record body | POST/PUT use `{"data": {...}}`. Response is `{"data":{"id":"...","data":{...}}}`. Creation 201, read/update 200, delete 204, missing GET 404. |
| Updates | The LLM guide mentions PATCH; reviewed OpenAPI omits project PATCH. Implement PUT only until that contract is verified. |
| Negative auth | Expect 401 for missing/invalid project keys; project live confirmation is pending. A WAF 403 is not automatic proof of API authorization behavior. |
| Free plan | Current LLM reference advertises 250 requests/day, 3 collections, 100 records, with daily reset at midnight UTC. These are advertised limits, not measured account entitlements. |
| Pricing uncertainty | `/pricing.md` could not be retrieved during review. Recheck the dashboard and current pricing before using quotas as a guarantee; no paid plan is required or purchased here. |
| Deletion | The spec includes an `include_deleted` query for record lists. GET 404 proves default API absence; it does not prove physical database erasure or reclaiming the record quota. |

The January QA blog has an unwrapped create example; the newer guide and OpenAPI
require the wrapper. Prefer the newer/spec-backed shape and record disagreements.
Do not copy `reqres-free-v1` from older tutorials as a private project credential.

## Scenarios and test pyramid

| ID / priority | Scenario | Expected result | Layer / marker |
| --- | --- | --- | --- |
| RD-01 / P0 | List two users → GET discovered ID | 200 schema; matching detail; no fixed ID/count | local/live; reqres_demo, smoke, contract |
| RD-02 / P1 | Two one-item pages | Correct page numbers; distinct discovered IDs | local/live; reqres_demo, boundary |
| RD-03 / P1 | Page after response's total_pages | 200 empty data array | local/live; reqres_demo, boundary |
| RD-04 / P1 | POST synthetic name/job | 201 echo plus string ID/createdAt; no persistence assertion | local/live; reqres_demo, regression |
| RP-01 / P0 | Create → GET → PUT → GET → DELETE → GET | Fields persist, including zero/false; 204 empty delete; 404 absence | local/live; reqres_project, workflow, contract |
| RP-02 / P1 | Create → search by unique name | Returned ID present; each result has our marker | local/live; reqres_project, regression, contract |
| RP-03 / P1 | POST with missing data wrapper | 400 JSON error; any unexpected returned ID is tracked before assertion | local/live; reqres_project, negative |
| RP-04 / P0 (2) | Missing / invalid project key on filtered read | 401; no inherited per-request key | local/live; reqres_project, negative |

Four demo cases send seven small requests per run. Five project cases normally
send fifteen requests and create two records; cleanup is included in that budget.
An unexpectedly accepted negative POST adds an identifiable record to teardown.
Provider traffic/quotas can include other callers and dashboard activity. Do not
try to measure a public limit by exhausting it.

The cheaper base covers header injection/repr safety, config/env precedence,
invalid path segments, strict finite/nonnegative prices and booleans, independent
payloads, malformed nested contracts, and redacted diagnostics. Seventeen real
loopback HTTP checks exercise cleanup failures, anonymous header isolation, and
429/Retry-After preservation for GET/POST/PUT/DELETE without request replay.

## Data and cleanup

The factory matches starter Products fields: name, price, category, in_stock.
Each name is `QA-<UUID>`; updates preserve it. Only returned test-created IDs may
be mutated/deleted. The suite neither changes collection definitions nor touches
seed records. A different schema needs an explicit factory/test change.

`RecordTracker` registers a usable string ID before status/schema/business checks.
The negative create test also registers an unexpected success. Teardown runs
before the request context closes. GET 404 is already absent; otherwise compare
`data.data.name` independently of unrelated metadata schema rules, DELETE, then
confirm GET 404. A changed/missing owner blocks deletion and fails cleanup. Try
remaining IDs after a failure and report safe aggregate errors without retries.

This is a separate tracker from Booker because response nesting, ID type, and
status conventions differ. Keep those differences visible instead of creating a
large generic resource framework. GET-then-DELETE is not atomic; process crashes,
unusable creation IDs, auth/network failures, or schema changes can prevent cleanup.

## Execution and acceptance

```bash
python -m pytest -m "reqres and not external"
python -m pytest tests/unit/test_reqres_policy.py tests/local/test_reqres_behavior.py
python -m pytest -m "reqres_demo and external" --run-external
python -m pytest -m "reqres_project and external" --run-external
```

The last command requires private project configuration; missing credentials fail
before HTTP, rather than converting requested live tests into a pass/skip. CI has
separate manual demo/project toggles and reports. No live job runs on push/PR.

Accept the implementation after local gates, package assets, maintained guides,
and CI pass. Describe project live compatibility as pending until the five project
cases actually run against the selected account. Advertised plan quotas and local
429 handling are distinct from live quota enforcement. No UI, MFA, public-key RBAC,
security audit, database validation, rate-limit stress, or retry-policy claim.
