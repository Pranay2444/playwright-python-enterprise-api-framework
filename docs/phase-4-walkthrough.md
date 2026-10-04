# Phase 4 learning walkthrough

## What changes from Phase 3?

Booker authenticates a per-test session with a cookie. ReqRes project requests use
a pre-provisioned API key plus an explicit project/environment. There is no login,
expiry timer, refresh token, or TokenManager for this key. The existing `ApiClient`
still sends the HTTP request and preserves failures.

| Code | Read it for |
| --- | --- |
| `src/api_framework/config.py` / ReqResSettings | Optional demo setup and required project setup |
| `clients/reqres/api_key.py` | Hidden repr, header validation, fresh header dict |
| `clients/reqres/demo_users_client.py` | Anonymous fixtures and simulated create |
| `clients/reqres/records_client.py` | Explicit key/env/project, wrapped data, safe IDs |
| `data/record_factory.py` | Strict starter product policy and synthetic marker |
| `contracts/reqres.json` | Partial service-specific response rules |
| `tests/reqres/conftest.py` | Separate demo/project targets and disposed contexts |
| `tests/support/record_lifecycle.py` | Early ID tracking, owner checks, cleanup |
| `tests/reqres/test_project_records.py` | PUT persistence and rejected requests |
| `tests/local/test_reqres_behavior.py` | Deliberate 429/cleanup/auth failures |

Paths in the table are relative to `src/api_framework` except where `tests/` is shown.

## Run without an account first

Activate the project's `.venv`, install the pinned dependencies and editable package
using the root README, then run:

```bash
python -m pytest -m "reqres and not external"
python -m pytest tests/unit/test_reqres_policy.py tests/local/test_reqres_behavior.py
```

LocalReqRes runs on a random loopback port and has fixture user IDs 71/82/93.
Tests discover IDs; those values are not in the live assertions. Its persistent
records last only until that test's server closes. Local success checks wiring,
not deployed behavior or your account's plan.

## Configure your own project

1. Open [ReqRes](https://app.reqres.in) yourself and create/select a dedicated free
   QA project. No key is supplied by this repository, and no paid plan is assumed.
2. Copy its manage key and project ID. Use the starter Products collection with
   name/price/category/in_stock fields, or an equivalent dedicated collection.
3. Fill the blank `REQRES_API_KEY` and `REQRES_PROJECT_ID` in your ignored `.env`.
   Keep `REQRES_COLLECTION=products` and `REQRES_ENV=prod` for the starter target;
   set dev only if you have created that environment.
4. Never paste a private key in chat, commit it, or print the environment. Process
   variables override this project's explicitly loaded `.env`.

```bash
python -m pytest -m "reqres_demo and external" --run-external
python -m pytest -m "reqres_project and external" --run-external
```

Demo calls send no project key, even when `.env` contains one. Project calls send
the key only in the `x-api-key` header, project ID through encoded query params,
and environment through `X-Reqres-Env`. Missing project config fails before HTTP.
If your plan/schema differs, inspect the current dashboard/docs before changing
expectations; do not substitute a demo create for a persistence test.

For GitHub Actions, use repository **Settings → Secrets and variables → Actions**:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | REQRES_API_KEY | Your QA project's manage key |
| Variable | REQRES_PROJECT_ID | Your QA project ID |
| Optional variable | REQRES_COLLECTION | products by default |
| Optional variable | REQRES_ENV | prod by default |

Then choose **Actions → API framework quality → Run workflow**, enable the ReqRes
project checkbox, and inspect its separate job/JUnit artifact. The demo checkbox
requires no secret. These toggles stay false on push/PR.

## Follow one persistent request

`record_tracker.create(product_record_data())` first creates a fresh strict payload.
RecordsClient wraps it as `{"data": payload}` and adds headers/query parameters.
ApiClient sends once with redirects/retries disabled. The response's outer data
contains a record whose inner data holds product fields.

```json
{
  "data": {
    "id": "returned-record-id",
    "data": {"name": "QA-unique-marker", "price": 9.99, "category": "Portfolio", "in_stock": true}
  }
}
```

The tracker stores that returned ID before schema/status assertions. A GET checks
the created fields; PUT changes price/category/stock while preserving name; a
second GET proves the changed fields are stored. DELETE expects 204 and no body,
then GET 404. Teardown confirms absence without deleting again.

Why preserve name? It is the test's ownership marker inside an existing permitted
field. Cleanup refuses to delete if the current record no longer carries it.
Marker checks reduce accidental deletion, but cannot make GET/DELETE atomic.
The API exposes deletion visibility, not a direct database erasure guarantee.

## Rate limits and honest failures

The current reference advertises 250 requests/day on Free with midnight UTC reset;
recheck your actual account limits. The project suite normally sends fifteen
requests. Do not run load loops or repeatedly rerun a failing public job.

The HTTP checks inject 429 and Retry-After locally. ApiClient returns both unchanged
and never automatically repeats GET/POST/PUT/DELETE. A caller can inspect the header
and decide when to explicitly run again; no backoff scheduler is implemented here.
A 429 during cleanup is a cleanup failure, not a reason to discard ownership tracking.

## Practice and explain

1. Trace `project_id` from `.env` to query params; explain why it never appears in logs.
2. Remove the data wrapper locally and observe the 400. Turn on the model's
   `accept_unwrapped_create` injection and see that unexpected success is cleaned up.
3. Change a tracked record's name in the local model; show why DELETE is withheld.
4. Run the zero-price/false-stock lifecycle and explain why truthiness checks would
   miss these values. Strict input types and response business assertions differ.
5. Compare the reviewed OpenAPI excerpt with the LLM guide. Explain the demo-auth
   and project-PATCH discrepancies before adding an unsupported expectation.

Interview explanation: “I extended one Playwright API framework across Bearer
tokens, cookie sessions, and API keys without mixing their lifecycles. I use cheap
policy and HTTP failure checks, then small live suites. Persistent records have
test-owned markers and tracked teardown, while public demo writes are explicitly
simulated. I report missing account configuration and rate-limit failures separately
from product defects.”

Read [the test plan](phase-4-test-plan.md), [contract guide](contracts.md), and
[validation record](validation.md) before claiming live or plan compatibility.
