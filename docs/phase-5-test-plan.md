# Phase 5 test plan: owned authentication and documents

Acceptance policy belongs to our disposable lab. No security/property test targets
a public provider. Preserve earlier phases' local and opt-in live scenarios. Read
[the strategy](testing-strategy.md) for the pyramid, [auth](phase-5-auth.md) for exact
transitions, and [validation](validation.md) for executed counts/run links.

## Risk and scenario mapping

| Domain / risk | Scenario and expected result | Source / layer |
| --- | --- | --- |
| Authentication: tokens before MFA | Password step 202 has only challenge; anonymous me 401 | `tests/lab/test_authentication.py`, actual HTTP |
| Authentication: wrong identity | Email, TOTP, mock SMS complete MFA; me matches returned user; logout invalidates old header | Same file + separate DB password/audit probe |
| Authentication: expiry | Challenge accepts at 119s, rejects at 120s; access rejects at 120s; family at 900s | Same file, controlled server/client clock |
| Authentication: guessing/replay | Three wrong password/OTP attempts; visible 429/Retry-After; consumed challenge and same TOTP step rejected | Same file, persisted policy |
| Authentication: forged refresh | Unknown digest 401 leaves real session usable | Same file, actual HTTP |
| Authentication: rotation/reuse | Explicit refresh succeeds; known old refresh revokes current family; client clears on refresh failure | Same file + `test_lab_session.py` |
| Authentication: claims/signature | Wrong signature/algorithm/issuer/audience/kind/time/types/missing claims rejected | HTTP tamper case + `test_lab_security.py` matrix |
| Authentication: provisioning | Extra role/tenant signup rejected; member admin gate 403, DB-provisioned admin 200 | Actual HTTP, controlled DB seam |
| Authentication: delivery failure | Broken adapter 503, challenge consumed, exception detail absent | Actual HTTP + DB observation |
| Authentication: unexpected failure | Injected verifier failure safe 500/correlation, client returns anonymous | Actual HTTP and LabSession composition |
| Authentication: code correlation | Exact recipient/subject/body; timeout and unsafe IDs; other user's code rejected | `test_mailpit_reader.py` + HTTP cross-challenge case |
| Documents: persistence/lifecycle | Upload 201; metadata/hash/owner/DB bytes; download exact bytes; delete204/GET404/DB absence | `tests/lab/test_documents.py` |
| Documents: access | Anonymous401; same/different tenant other user404; owner unchanged | Same file, HTTP + DB probe |
| Documents: unsafe input | Traversal/bad name422; MIME415; empty/oversize413; invalid UTF-8/NUL422; exact 65536-byte file201 | Same file, no persistence on rejected filenames |
| Documents: idempotency | Same key and content200/same ID; changed content/name409; one audit | Same file, HTTP + DB probe |
| Persistence: races | Two verifications yield200/401/one session; refresh200/401/revoked family; duplicate upload201/200/one row and audit | Auth concurrency file and document race |
| Persistence: lock order | Concurrent login202 and old verification200 or401 complete; at most one old session | `tests/lab/test_concurrency.py` |
| Contracts: response schema | Selected me/upload response validates against app OpenAPI3.1; injected wrong size rejected safely | Document schema case + `assertions/openapi.py` |
| Contracts: generated inputs | Twelve bounded wrong-password-type HTTP examples422/no user; fifty filename and thirty extra-role policy examples | `test_generated_contracts.py` + unit Hypothesis |
| Framework: client failure | Bad provider/token controls/refresh clear state; logout failure clears but remains visible | `tests/unit/test_lab_session.py` |
| Framework: reporting | Setup/call/teardown routed safely; worker isolation; parameters discarded; unwritable path preserves original failure | `tests/unit/test_defect_reporting.py` |
| Framework: deployment | Installed container email MFA → document checksum/delete → refresh/logout | `tests/deployment/test_lab_container.py` |

Property examples are examples **inside** a test; they are not added to the Pytest
case count. Generated HTTP negatives reuse a function-scoped app deliberately:
each rejected request creates no user, which is checked after every example.
Schemathesis, exhaustive fuzzing, performance benchmarks, TLS deployment, and UI
are not implemented. OpenAPI checks cover selected JSON responses, not every route,
request, header, or the generator's independent correctness.

## Execution targets and oracles

| Target | App and delivery | Database | Evidence / limitation |
| --- | --- | --- | --- |
| Default owned fixture | Actual FastAPI/Uvicorn HTTP; captured email/mock SMS | Temporary SQLite | Deterministic policy and composition, no real SMTP/PG row-lock claim |
| PostgreSQL/Mailpit flags | Actual per-test app; real SMTP, correlated Mailpit read | Random per-test PostgreSQL schema | Real driver, locking, uniqueness, schema lifecycle; two workers |
| Deployment flag | Installed Docker app; real SMTP/Mailpit; real wall clock | Compose PostgreSQL app schema | End-to-end infrastructure smoke, no clock/DB injection |
| Earlier provider `[local]` | Small public-service doubles | Their local model | Framework wiring, not deployed provider proof |
| Earlier provider `[live]` | Opt-in real services | Provider-owned | Point-in-time compatibility, account config required for ReqRes project |

API oracle checks returned fields/status/bytes. A separate DB session checks rows,
content, hashes and event names without calling business service methods. It shares
ORM definitions; no full migration/schema verification is claimed. Schema creation
and role changes are controlled test seams, never public backdoors.

## Data, isolation, and teardown

Fresh UUID emails ending `@example.test`, synthetic passwords, per-test signing
keys and text bytes; never real documents/accounts/phone numbers. A schema owner
fixture tears down even when table creation/app setup fails. Worker IDs are used
only for safe report routing; random DB schemas/ports provide actual isolation.
The Mailpit callback binds recipient **and challenge**, so messages from another
test are ignored. Do not purge a shared mailbox between tests.

Default fixture teardown removes the entire test database/schema after stopping
requests/server. Deployment teardown tracks and deletes the test's returned
document, and logs out; synthetic accounts/audit rows remain until the CI volume
reset. Unusable IDs/process termination/teardown transport failure cannot guarantee
document cleanup. Preserve those failures instead of searching/deleting unrelated data.

## Exit checks

```bash
ruff check .
ruff format --check .
python -m pytest -m 'not external and not deployment' --junitxml=reports/local-results.xml
python -m pytest tests/lab -n 2
python -m build
python scripts/check_wheel.py
python scripts/check_docs.py
```

Then execute the [owned-stack commands](phase-5-walkthrough.md#postgresql-and-real-smtp-tests)
in CI. Success requires actual PostgreSQL+SMTP and the installed container smoke,
not merely a YAML parse or SQLite substitute. Inspect all three Python matrix jobs,
owned job, and artifact upload. Record exact outcomes and any repaired failure.
The five private ReqRes live cases remain pending user account configuration;
that unrelated missing credential is never replaced with a tutorial key or described
as a pass. Prior phases' validation records remain historical evidence.
