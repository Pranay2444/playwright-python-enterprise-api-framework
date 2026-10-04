# Repository instructions for coding assistants

This is a Phase 3 Python Playwright API automation learning/portfolio project.
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

## Verification

Run the relevant test while editing. Before completing a code change, run:

```bash
ruff check .
ruff format --check .
python -m pytest -m "not external"
python -m build
```

Use `python -m pytest -m external --run-external` only when live verification is
requested and available. State which target ran; never describe local test-double
results as a live service pass. Update the test plan for new behavior.

## Defects and RCA

Classify product, framework, data, and environment failures using evidence. Keep
observations, hypotheses, and confirmed causes separate. Use the defect report
template. Do not publish issues/comments or message people unless asked to do so.

## Project-specific facts

- DummyJSON writes are simulated. Do not require read-after-write cart persistence.
- Public product/user/cart endpoints are not authorization enforcement evidence.
- Token expiry here is a requested-duration scheduling hint, not JWT verification.
- Partial response contracts and negative/boundary tests are implemented in Phase 2.
- Persistent booking lifecycle, independent auth, and owned-resource cleanup exist in Phase 3.
- Booker uses 200 create/read/PUT/PATCH, 201 delete/ping, and 403 anonymous writes.
- Its shared demo resets periodically: check ownership before deleting; GET/DELETE is not atomic.
- Security fuzzing, MFA, DB checks, and UI are future phases.
- The synchronous `TokenManager` is not thread-safe. Do not share it across threads.
