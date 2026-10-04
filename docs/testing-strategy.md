# Phase 1 testing strategy

## Goal and scope

Prove the framework is maintainable and that its clients can exercise the documented
DummyJSON auth/product/user/cart flows. Distinguish framework defects from public
service failures. Use a repeatable local base and a small live service suite.

Phase 1 includes basic shape/business assertions. It excludes formal JSON Schema or
OpenAPI contracts, performance SLAs, RBAC, database verification, MFA, UI flows, and
security fuzzing. Do not describe these exclusions as implemented capabilities.

## Test pyramid

| Layer, from broad base upward | Checks | Why this layer |
| --- | --- | --- |
| Unit | Cache reuse, timed refresh, failure invalidation, independent managers, config validation, payload isolation | Fast feedback without driver/network dependencies |
| Local HTTP integration | Real Playwright requests, cookie/Bearer isolation, query encoding, exposed HTTP errors, transport error redaction | Verify components work together without public-service availability |
| Live API functional/workflow | Eleven selected DummyJSON scenarios | Confirm current real endpoint behavior and dynamic response chaining |
| UI E2E | None in Phase 1 | Add only critical browser journeys when UI scope is introduced |

Treat the pyramid as an allocation of feedback cost and risk, not a fixed percentage.
Local functional scenarios exercise the same client/test code as live scenarios,
but do not prove a public contract. The local server must not become a replacement
for integration verification against the real service.

## Risk-driven coverage

| Risk | Coverage now | Additional coverage later |
| --- | --- | --- |
| Incorrect identity after login/refresh | User identity checks and proactive refresh tests | Missing/expired/wrong-token negative cases |
| Cookie contamination hides missing Bearer auth | Separate contexts and a local 401 isolation test | Live missing-auth checks using fresh contexts |
| Shared cache creates cross-test identity errors | Function scope and independent-manager tests | Worker/process execution validation |
| Hardcoded IDs break when data changes | Discover IDs from responses; nonstandard local fixture IDs | API-created lifecycle data in owned/persistent services |
| HTTP wrapper hides service failures | Return 4xx/5xx without retries; assert status in tests | Explicit bounded retry policy for approved idempotent requests |
| Simulated cart mistaken for persistence | Validate only the add response; document limitation | Persistent booking/local FastAPI CRUD lifecycle |
| Secrets leak into diagnostics | No query/header/body logs; sanitized transport exceptions; masked token/settings repr | Broader artifact redaction once richer reporting is introduced |
| Public endpoint outage blocks all development | Deterministic CI and separate opt-in live job | Scheduled service checks after reliability/cost review |

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

Do not replay business requests after 401, 429, 5xx, or transport failures in Phase 1.
Disable automatic redirects/retries. Expose failures to the test and classify them
using the defect agent. A refreshed token can be used by a subsequent explicit call.

## Quality gates

| Gate | Required evidence | Result |
| --- | --- | --- |
| Local change | Relevant tests; no linter/formatter failures | Ready for broader local validation |
| PR / push | Lint + formatting + deterministic suite on configured Python matrix | Framework quality signal |
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

## Phase 1 exit criteria

1. Local framework/unit/functional checks pass through real Playwright transport.
2. Auth is isolated per test and refresh behavior has deterministic clock coverage.
3. Eleven live-capable functional scenarios have explicit expected results.
4. Formatting/lint and package build checks pass.
5. Setup, fixture lifecycle, test selection, and service limitations are documented.
6. Live results are recorded honestly. If network blocks execution, mark live
   compatibility as pending rather than claiming a full real-service pass.
