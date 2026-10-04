---
name: api-test-strategy
description: Plan and add tests in this Python Playwright API portfolio using risk-based coverage, the test pyramid, dynamic data, and isolated fixtures. Use when designing an endpoint test, extending a client, reviewing coverage, or preparing a phase test plan.
---

# Plan and implement API coverage

1. Read the repository README and [testing strategy](../../../docs/testing-strategy.md).
   Inspect the current [test plan](../../../docs/test-plan.md) and the relevant client/tests.
2. Confirm the endpoint's current official contract. Separate documented behavior,
   project expectations, and unverified assumptions. Check service limitations before
   planning persistence, authorization, or negative scenarios.
3. Identify the concrete quality risk. Choose the cheapest useful layer: unit for
   isolated policy, local HTTP for framework composition, live API for real service
   compatibility. Reserve UI E2E for future critical browser journeys.
4. Specify method/path, preconditions, status, response fields, business relationships,
   data source, target, cleanup, and markers. Refer to the test pyramid; avoid fixed
   public IDs, complete snapshots, and exact catalogue totals.
5. Add the smallest domain-client method and test needed. Return `APIResponse`.
   Keep assertions in the test and fresh payload creation in a factory. Use Pytest
   fixture injection and preserve separate auth/public contexts.
6. Extend the local HTTP model only enough to check wiring. Do not treat model
   agreement as proof of a public contract. Add or retain an equivalent live case.
7. Run the focused local test, `ruff check .`, `ruff format --check .`, and the local
   suite. Run external tests only with explicit opt-in and an available network.
8. For Phase 2 contracts, read `docs/contracts.md`. Use named JSON Schemas for
   structure and tests for business relationships. Inject malformed nested data in
   unit tests to prove rejection. Avoid full snapshots and leaking validation inputs.
9. Distinguish strict factory policy from service rules. Negative API tests must
   bypass the valid factory and use an anonymous context when testing missing auth.
10. For persistent bookings, read [the Phase 3 plan](../../../docs/phase-3-test-plan.md).
    Use independent Booker fixtures/session headers. Create synthetic data only;
    register returned IDs before response assertions; keep the lastname marker unchanged.
    Verify read-after-write and GET 404 after deletion. Finalize before contexts close.
    Prove cleanup under assertion/schema failure with loopback injection. Verify ownership
    before deleting; continue other tracked IDs and report failures without retries.
11. For ReqRes, read [the Phase 4 plan](../../../docs/phase-4-test-plan.md).
    Separate anonymous demo fixtures/simulated writes from project-key persistent records.
    Use explicit project/env config and a user-owned manage key; never include it in URLs,
    logs, or checked-in files. Wrap record POST/PUT data and discover returned string IDs.
    Preserve synthetic names and track unexpected success in negative create tests.
    Keep 429/Retry-After visible; test failures locally instead of exhausting public quotas.
    Distinguish reviewed OpenAPI, conflicting docs, advertised limits, and live evidence.
12. For the owned lab, read [workflow](../../../docs/phase-5-workflow.md),
    [authentication](../../../docs/phase-5-auth.md) and [the Phase 5 plan](../../../docs/phase-5-test-plan.md).
    Choose unit policy, actual HTTP composition, PostgreSQL/SMTP integration or installed
    container checks by risk. Inject clock/delivery through the app factory only;
    no OTP/time/role HTTP bypass. Use explicit LabSession state and no business replay.
    Keep per-test schemas/ports/contexts and per-thread Playwright drivers. Retain
    challenge/token CAS, consistent user-first locks, replay history and DB uniqueness.
    Use bounded generated cases on owned endpoints only; distinguish shared OpenAPI
    agreement from independent contract evidence. SMS is mock delivery, never real recipients.
13. Route failed evidence using [domain triage](../../../docs/defect-management.md).
    Discard parameter values before hashing; never copy exception/body/secret fields.
    Preserve original failures when artifacts fail. Do not publish issues/messages.
14. Update the plan and report commands/results/limitations. Verify installed-wheel
    behavior and actual PostgreSQL/SMTP/container CI before claiming those capabilities.
    Keep five private ReqRes live cases pending until configured and executed.
    Sync repository skill edits in git; this does not install a personal skill.

For DummyJSON, validate simulated cart-add responses without persistence claims.
Keep login tokens in memory, per test. Preserve HTTP failures and avoid automatic
business-request replay. Route failures to `agents/defect-triage.agent.md` at the
repository root; do not hide them with skips or retries.

Produce a concise plan containing: risk, layer, scenario, data/preconditions,
expected result, marker/target, cleanup, and verification command. Follow it with
the implemented change and executed evidence when implementation is requested.
