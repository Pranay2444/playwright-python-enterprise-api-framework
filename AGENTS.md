# Repository instructions for coding assistants

This is a Phase 5 Python Playwright API automation learning/portfolio project.
Read README.md and docs/validation.md before describing its capabilities.

## Change approach

- Use `.agents/skills/api-test-strategy/SKILL.md` when planning or adding tests.
- Use `agents/defect-triage.agent.md` when investigating failures or preparing RCA.
- Follow existing `src/api_framework` package boundaries. Keep code short and explicit.
- Keep business assertions in tests, endpoint details in clients, HTTP concerns in core.
- Discover public resource IDs at runtime; do not copy fixed IDs from examples.
- Preserve function-scoped contexts/tokens and the separate login-cookie context.
- Add only abstractions needed by the current phase. Do not scaffold future providers.
- Mark live-target cases `external`; do not contact public services without explicit
  live execution. Keep public checks small and within documented behavior.
- Do not log tokens, cookies, passwords, body dumps, or private query values.
- Never turn a failing assertion into a skip or add retry loops to hide a failure.
- Use `contract_json` for supported JSON response contracts; retain business assertions.
- Allow additive response fields. Keep JSON Schema and typed product constraints aligned.
- Use strict Pydantic models for valid generated inputs, raw dicts for negative API tests.
- Separate our positive-quantity input policy from DummyJSON's permissive validation.
- Keep Booker cookie sessions separate from DummyJSON's TokenManager; no invented refresh.
- Use `booking_tracker` for persistent Booker creations. Register IDs before schema
  assertions, preserve the unique synthetic lastname marker, and finalize before contexts close.
- Never mutate/delete shared seed bookings or enumerate the shared dataset for cleanup.
- Cleanup must verify ownership and absence, attempt other tracked IDs after failure,
  and surface failures. Do not add retries or treat a changed marker as successful cleanup.
- Never include jsonschema error messages/instances or Pydantic `.errors()` input values
  in shared diagnostics; read docs/contracts.md before extending validation.
- Keep ReqRes demo and project surfaces separate. Never claim demo writes persist.
- Project tests require user-owned manage-key/project/env config; never hardcode or
  substitute a tutorial key. Attach the key per request; keep it out of URLs/logs/repr.
- Preserve ReqRes synthetic product name markers; track IDs before assertions,
  including unexpected success from negative create tests; verify ownership/absence.
- Use project PUT only: reviewed OpenAPI does not declare project PATCH. Check
  current provider evidence before extending it or assuming a plan entitlement.
- Keep 429/Retry-After visible without replay. Do not exhaust public quotas to test them.
- For the owned lab, read docs/phase-5-workflow.md, docs/phase-5-auth.md and the Phase 5 plan.
- Keep actual app rules in framework_lab services, endpoint details in lab clients,
  and business assertions in tests. Use explicit LabSession transitions, not TokenManager.
- Inject time/delivery through create_app only; never add HTTP OTP/time/role backdoors.
- Use synthetic @example.test recipients, captured SMS only, and no real documents.
- Keep user-before-challenge lock order, unused-row CAS, TOTP step replay protection,
  refresh-token history and owner/idempotency uniqueness. Never replace these with sleeps.
- Each worker/test owns its schema/port/contexts; each race thread owns a Playwright driver.
- Drop only the fixture-owned schema; Compose volume reset belongs only to a disposable stack.
- Receipts discard parameter suffixes before hashing. Preserve original failures if reporting fails.
- Do not claim SQLite/captured-delivery checks prove PostgreSQL/SMTP/container execution.

## Verification

Run the relevant test while editing. Before completing a code change, run:

```bash
ruff check .
ruff format --check .
python -m pytest -m "not external and not deployment"
python -m pytest tests/lab -n 2
python -m build
python scripts/check_wheel.py
python scripts/check_docs.py
```

Use `python -m pytest -m external --run-external` only when live verification is
requested and available. State which target ran; never describe local test-double
results as a live service pass. Update the test plan for new behavior.

## Defects and RCA

Classify product, framework, data, and environment failures using evidence. Keep
observations, hypotheses, and confirmed causes separate. Use the defect report
template. Do not publish issues/comments or message people unless asked to do so.
Use docs/defect-management.md and agents/domains/*.agent.md for domain routing;
guides do not launch agents. Separate setup/call/teardown evidence and human RCA.

## Project-specific facts

- DummyJSON writes are simulated. Do not require read-after-write cart persistence.
- Public product/user/cart endpoints are not authorization enforcement evidence.
- Token expiry here is a requested-duration scheduling hint, not JWT verification.
- Partial response contracts and negative/boundary tests are implemented in Phase 2.
- Persistent booking lifecycle, independent auth, and owned-resource cleanup exist in Phase 3.
- Booker uses 200 create/read/PUT/PATCH, 201 delete/ping, and 403 anonymous writes.
- Its shared demo resets periodically: check ownership before deleting; GET/DELETE is not atomic.
- ReqRes project adapter is implemented; live compatibility needs configured credentials
  and an executed live result. Default GET 404 does not prove physical record erasure.
- ReqRes's current LLM reference and older OpenAPI/docs disagree on demo auth; keep
  observed failures and expectations separate. See docs/phase-4-test-plan.md.
- Owned-app MFA/files, bounded security/property checks, database probes and parallel
  execution are Phase 5. UI, exhaustive fuzzing, performance SLAs and production
  identity operations remain outside this portfolio release.
- The synchronous `TokenManager` is not thread-safe. Do not share it across threads.
