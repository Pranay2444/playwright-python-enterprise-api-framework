# Testing strategy through Phase 3

## Goal and scope

Prove the framework is maintainable and that its clients can exercise the documented
DummyJSON auth/product/user/cart flows and Restful Booker persistent bookings. Distinguish framework defects from public
service failures. Use a repeatable local base and a small live service suite.

Phases 2/3 add partial JSON Schema response contracts, strict Pydantic views/inputs,
negative/boundary checks, a second auth style, and tracked persistent-resource cleanup.
The current scope excludes exhaustive OpenAPI/provider verification,
performance SLAs, RBAC, database verification, MFA, UI flows, and security fuzzing.

## Test pyramid

| Layer, from broad base upward | Checks | Why this layer |
| --- | --- | --- |
| Unit | Cache reuse, timed refresh, failure invalidation, independent managers, config validation, payload isolation, malformed schema/model inputs, diagnostic redaction | Fast feedback without driver/network dependencies |
| Local HTTP integration | Real Playwright requests, cookie/Bearer isolation, query encoding, exposed HTTP errors, transport error redaction, persistent CRUD wiring, cleanup failure injection | Verify components work together without public-service availability |
| Live API functional/contract/negative/boundary | 32 DummyJSON + 10 Booker cases; seven synthetic bookings per Booker run | Confirm current real endpoint behavior and dynamic response chaining |
| UI E2E | None through Phase 3 | Add only critical browser journeys when UI scope is introduced |

Treat the pyramid as an allocation of feedback cost and risk, not a fixed percentage.
Local functional scenarios exercise the same client/test code as live scenarios,
but do not prove a public contract. The local server must not become a replacement
for integration verification against the real service.

## Risk-driven coverage

| Risk | Coverage now | Additional coverage later |
| --- | --- | --- |
| Incorrect identity after login/refresh | Identity checks, proactive refresh, invalid/missing login and token rejection | Owned-app expiry/signature/access policy checks |
| Cookie contamination hides missing Bearer auth | Separate contexts, local isolation regression, local/live missing-auth scenarios | Broader owned-app auth policy |
| Shared cache creates cross-test identity errors | Function scope and independent-manager tests | Worker/process execution validation |
| Hardcoded IDs break when data changes | Discover IDs from responses; nonstandard local fixture IDs | API-created lifecycle data in owned/persistent services |
| HTTP wrapper hides service failures | Return 4xx/5xx without retries; assert status in tests | Explicit bounded retry policy for approved idempotent requests |
| Simulated cart mistaken for persistence | Validate only the add response; document limitation | Persistent booking/local FastAPI CRUD lifecycle |
| Secrets leak into diagnostics | No query/header/body logs; sanitized transport/schema exceptions; hidden model input errors; masked token/settings repr | Broader artifact redaction once richer reporting is introduced |
| Persistent data survives failed assertions | Track IDs before contract checks; fixture teardown; owner checks; verify 404; visible cleanup failures | Owned-app atomic cleanup and durable resource ownership |
| Cookie auth forced into Bearer lifecycle | Dedicated Booker session and anonymous client; no invented refresh | Additional auth adapters only when needed |
| Public endpoint outage blocks all development | Deterministic CI and separate opt-in live job | Scheduled service checks after reliability/cost review |
| Shape drift hidden by ad hoc assertions | Partial response schemas; strict typed views; malformed nested unit cases | Additional service-specific contracts |
| Invalid data blocked before reaching a rejection test | Strict valid factories; raw dictionaries for server negatives | Owned-app validation matrices |

## Data and environment approach

- Use environment variables as the highest-precedence configuration. Load only the
  repository's explicitly selected `.env`; never search parent projects for one.
- Accept only an HTTP(S) origin. Keep credentials out of URLs.
- Treat `emilys` / `emilyspass` as published demo credentials, not private accounts.
- Discover product/user/cart IDs at runtime. State minimum data prerequisites in tests.
- Rebuild the local server per test, using a random loopback port.
- Keep request contexts, tokens, and payloads per test. Dispose contexts even after failures.
- For simulated writes, do not add meaningless cleanup calls. Real persistent writes
  in future phases must track created resources and clean them up in fixture teardown.

## Authentication and failure policy

Acquire tokens lazily through `TokenSource`. Cache access/refresh tokens in memory.
Refresh before the requested lifetime expires using an injectable monotonic clock;
test timing without real sleeps. The server remains the authority on validity.
Do not use this local timing policy as evidence that a JWT signature was verified.

Do not replay business requests after 401, 429, 5xx, or transport failures in the implemented phases.
Disable automatic redirects/retries. Expose failures to the test and classify them
using the defect agent. A refreshed token can be used by a subsequent explicit call.

## Quality gates

| Gate | Required evidence | Result |
| --- | --- | --- |
| Local change | Relevant tests; no linter/formatter failures | Ready for broader local validation |
| PR / push | Lint + formatting + distribution build + deterministic suite on configured Python matrix | Framework quality signal |
| Manual live run | Live suite with explicit external opt-in and network access | Real-service compatibility signal |
| Phase completion | Test plan mapped to scenarios, truthful validation notes, reviewed docs | Portfolio milestone can be described accurately |

The CI workflow defines jobs, not repository branch protection. Do not say a merge
is prevented unless required status checks are configured by the owner.

## Diagnostics and triage

Capture the command, target, test node ID, version, timestamp, endpoint/method/status,
and safe timings. Avoid raw tokens, passwords, cookies, and entire auth responses.
Never turn assertions into skips or increase retries simply to make a run green.
Keep confirmed facts, hypotheses, and missing evidence separate in RCA reports.

Use [the defect report template](templates/defect-report.md) and the repository
agent instructions. Reproduce with the smallest test before changing the framework.

## Phase 1 foundation criteria (retained)

1. Local framework/unit/functional checks pass through real Playwright transport.
2. Auth is isolated per test and refresh behavior has deterministic clock coverage.
3. Eleven live-capable functional scenarios have explicit expected results.
4. Formatting/lint and package build checks pass.
5. Setup, fixture lifecycle, test selection, and service limitations are documented.
6. Live results are recorded honestly. If network blocks execution, mark live
   compatibility as pending rather than claiming a full real-service pass.

## Phase 2 exit criteria

1. Existing functional responses have named contracts; business assertions stay in tests.
2. Validators detect missing/nested wrong fields and expose safe, distinct errors.
3. Pydantic rejects coercion in generated payloads and typed product views.
4. Rejected requests and boundaries execute on both local/live targets with explicit markers.
5. Wheel/source distributions include schema assets; an installed-wheel probe succeeds.
6. Detailed contract basis, limitations, maintenance, and learning guides are documented.
7. Deterministic and live execution evidence is recorded separately.

See [the Phase 2 plan](phase-2-test-plan.md) for scenario/data/status mapping and
[contract maintenance](contracts.md) for input policy versus provider behavior.

## Phase 3 exit criteria

1. Shared transport supports a second service without mixing tokens/config/fixtures.
2. Create/read/PUT/PATCH/delete persist, and deletion is verified by GET 404.
3. Public mutations touch only bookings created by that test; synthetic markers survive updates.
4. Cleanup tracks IDs early, checks ownership, continues other resources on failure, and fails visibly.
5. Loopback failure injection proves cleanup after test/schema failures and rejects ID reuse.
6. The Booker schema survives distribution builds, and API/array checks remain redacted.
7. Existing local/live coverage remains intact; each service has a distinct opt-in CI result.

A shared demo reset is a data/environment possibility, not automatic proof of an
application defect. Do not add retries or broaden cleanup to search/delete seed data.
See [the Phase 3 plan](phase-3-test-plan.md) for cleanup limits and evidence.
