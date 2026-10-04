# Incremental roadmap

| Phase | Add only when starting that phase | Exit evidence |
| --- | --- | --- |
| 1 | Core transport, config, auth/token lifecycle, DummyJSON clients, dynamic data, local/live tests, CI | Local checks and package build pass; live state recorded honestly |
| 2 — implemented | JSON Schema response validators and strict Pydantic views/inputs; negative credentials/auth; invalid IDs/method; boundaries | Validator fault injection, local/live target cases, safe diagnostics, packaged schema, documented status expectations |
| 3 — implemented | Restful Booker adapter, isolated cookie session, lifecycle fixtures, ownership checks | Create → get → put → patch → delete; verify deletion; robust cleanup of created booking |
| 4 | ReqRes adapter after checking current official key/account/plan rules | A different auth style works through shared transport; persistence/rate rules verified for chosen plan |
| 5 | Owned FastAPI e-commerce/test app and Docker setup | Persistent API flows, PostgreSQL checks, controlled auth and failure injection |
| 6 | Mailpit/email OTP, TOTP, mock SMS, file upload/download | Correlated OTP retrieval, deterministic clock handling, checksum/file metadata validation |
| 7 | Owned-environment security/property/contract fuzzing | RBAC/cross-user/expiry/rate-limit cases; controlled Schemathesis/Hypothesis findings |
| 8 | Process parallelism and richer reports | Isolated workers/resources, safe attachments, stable CI artifacts |

Do not scaffold every provider or service before its first concrete test. Keep core
changes driven by real usage. For example, add a retry policy only alongside tests
that establish which methods can be retried, how many times, how `Retry-After` is
interpreted, and how failures remain visible.

The test pyramid should remain broad at the inexpensive layers. Add browser E2E
only for a few critical user journeys if UI scope is introduced; do not copy all API
cases into UI tests.

Live/public service behavior and access requirements may change. Verify current
official contracts when beginning each adapter. Roadmap entries are goals, not
claims about current service plans or guarantees.
