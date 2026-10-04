# Five-phase portfolio roadmap

The user's final Phase 5 combines the former roadmap's Phases 5–8 core into one
maintainable owned lab release. No separate Phase 6–8 implementation is required.

| Phase | Implemented capability | Exit evidence |
| --- | --- | --- |
| 1 | Core transport/config, DummyJSON clients, scoped token lifecycle, dynamic data, CI | Local/package and point-in-time live results |
| 2 | Partial JSON Schema, strict Pydantic, negative and boundary checks | Fault injection, packaged assets and local/live scenarios |
| 3 | Booker adapter/cookies, persistent lifecycle and owned cleanup | CRUD/PATCH/GET absence, failure-safe cleanup and live evidence |
| 4 | ReqRes demo/project clients, API keys, contracts, records, local429 checks | Local/package/CI and demo live; five private project cases pending account config |
| 5 — final | Owned FastAPI/SQLAlchemy auth/document app, JWT/MFA, PostgreSQL/Mailpit/Docker, bounded security/Hypothesis, parallelism and domain reports | Full local/matrix/wheel checks, actual PG/SMTP/container CI, comprehensive layer/auth/triage docs |

See [validation](validation.md) for executed outcomes and limitations, and the
[Phase 5 plan](phase-5-test-plan.md) for risk-to-scenario mapping. Code and workflow
configuration do not substitute for an executed result.

Optional extensions after the five-phase release include a few critical browser
journeys, independently reviewed complete contracts, Schemathesis, performance
benchmarks, migrations/retention, and production identity operations. These are
unimplemented choices, not promises or current coverage. Real SMS is outside scope.

Keep the test pyramid broad at inexpensive layers. Add only abstractions needed
by a concrete scenario. A retry policy would need explicit method/attempt/failure
semantics and dedicated evidence; this framework currently exposes failures without
business replay. Security/property checks belong to owned environments, not public
quota exhaustion. Recheck current official contracts before extending a public adapter.
