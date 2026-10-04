# Phase 5 implementation checkpoint — 4 October 2026

Historical checkpoint: the resumed Phase 5 release is described in
[the workflow guide](../phase-5-workflow.md) and [validation records](../validation.md).
The tasks and counts below describe the saved draft, not current completion status.

At checkpoint time, this was unfinished work on a draft branch. Phase 4 remains the published release on
main. Resume this checkpoint to complete the user's final Phase 5 request; do not
report this branch as a finished release.

## Requested outcome

Build Phase 5 extensively in the same repository, keeping Python readable and
maintainable. Handle authentication carefully. Add a separate Markdown explanation
of project workflows, design patterns, and communication between layers. Add a
project-level defect reporting mechanism divided into domains, with triage/RCA
instructions. Existing authorization covers publishing completed code to the same
GitHub repository; no new repository or repeated approval is needed.

The earlier roadmap had owned FastAPI, MFA/files, security/property tests, and
parallel reporting spread across Phases 5–8. The final Phase 5 combines that core
scope. Real SMS gateways, production-grade identity operations, browser UI,
performance SLAs, and exhaustive fuzzing remain outside this lab release.

## Implemented, locally checked

- Version 0.5.0 packaging metadata; lab/dev extras and refreshed exact dependency lock.
- Owned FastAPI package `src/framework_lab`, using SQLAlchemy/SQLite or PostgreSQL.
- Synthetic signup, Argon2 password hashes, password-first MFA challenges, email
  delivery via SMTP adapter, controlled TOTP, and an explicitly injected mock SMS adapter.
- Keyed OTP hashes, attempt budgets, expiry, challenge invalidation, atomic OTP
  consumption, persistent TOTP step replay protection, password lockout/Retry-After.
- HS256 JWT verification with pinned algorithm, required issuer/audience/identity
  and temporal claims against an injected server clock; DB-backed session revocation.
- Hashed opaque refresh tokens, explicit rotation, known-token reuse revoking the
  session family, unknown forged refresh tokens rejected without revoking valid sessions.
- User/tenant ownership checks; member versus provisioned-admin access policy.
- Bounded UTF-8 `.txt` uploads, body bound before multipart parsing, DB-backed content,
  checksum/metadata/download/delete, DB uniqueness for concurrent idempotent uploads.
- `LabAuthClient`, `DocumentsClient`, and fail-closed `LabSession`, reusing the existing
  ApiClient. Multipart is the only shared transport extension. No business replay.
- Correlated Mailpit reader, selected OpenAPI JSON response validation with safe errors.
- Per-test real Uvicorn loopback fixtures, controlled clock, temporary SQLite DB;
  optional disposable PostgreSQL schema and SMTP/Mailpit flags.
- Opt-in domain failure receipts via pytest plugin; setup/call/teardown kept separate,
  parameter values hashed rather than copied, no exception text or response body.
- Authentication/documents/concurrency/unit/property/reporting tests. Focused batches:
  60 passed, followed by 8 passed. Lint and formatting pass (114 Python files checked).
- Full checkpoint suite: **271 passed; 51 live cases deselected in 28.00 seconds**.

## Important limitations to explain and inspect

This is an owned, disposable authentication/document lab. It is not a production
identity service. TOTP enrollment is simplified and returns the secret once during
synthetic signup; the lab stores TOTP secrets in the DB without a KMS encryption
layer. No public debug endpoint exposes OTPs or allows role/tenant assignment.
The injected test clock belongs to the application factory, not an HTTP endpoint.
Default local email delivery is in-memory; real SMTP and PostgreSQL compatibility
still require execution in CI. SMS is simulated, never delivered to a real phone.
Do not claim schema self-consistency proves an external contract. Files use one
small DB transaction; they do not claim malware scanning, object storage, or bulk throughput.

## Next work, in dependency order

1. Finish focused coverage: unit-test Mailpit recipient/subject/body correlation,
   timeout, unsafe IDs; add HTTP tampered-JWT rejection and HTTP/audit correlation.
   Check `LabSession` rejects control characters in token responses. Consider strict
   six-digit OTP validation and clear type annotations on clients/services.
2. Add `scripts/init_lab.py` generating a private signing key without echoing or
   overwriting it. Support `LAB_SIGNING_KEY_FILE` in settings for Compose secrets.
   Ignore `lab/.secrets`, `.db`, and Hypothesis artifacts in git; exclude secrets from
   Docker context. Never commit generated keys.
3. Add `lab/Dockerfile` using a non-root Python 3.12 app and root `compose.yaml` with
   PostgreSQL, Mailpit, and app. Bind host ports to loopback. Suggested ports:
   PostgreSQL 5440, SMTP 1025, Mailpit 8025, app 18080. PostgreSQL healthcheck and app
   DB readiness; verify Mailpit's image healthcheck before depending on it. A current
   official package lookup showed Mailpit v1.31.3, but verify its image availability.
   No Docker binary exists in this workspace, so actual build/start checks belong in CI.
4. Add an explicit `deployment` marker and `--lab-container` opt-in plus loopback
   `--lab-base-url`. Add an owned-container smoke flow: register -> password ->
   correlated Mailpit OTP -> me -> upload/download checksum -> delete/GET404 ->
   refresh -> logout. Report cleanup errors and close contexts in finally.
5. Update quality selectors to `not external and not deployment`. Add an owned-lab
   CI job that builds/starts Compose, runs real PostgreSQL+Mailpit lab tests with two
   xdist workers, and exercises the app container smoke flow. Upload safe failure
   receipts and JUnit. Shutdown only that job's disposable stack/volume. Leave
   public live suite opt-ins separate, and do not require missing private ReqRes keys.
6. Write `docs/phase-5-workflow.md`, an extensive walkthrough/auth guide, test plan,
   domain defect/RCA guide and templates/issue forms. Explain composition root,
   dependency injection, service layer, delivery adapters, fixtures, API versus DB
   oracles, explicit client states, bounded delivery polling versus business retry,
   transaction/CAS/uniqueness concurrency controls, and worker resource isolation.
   Add domain agent guides if useful; guides do not launch agents or publish issues.
7. Update README, docs/src/tests maps, roadmap (final Phase 5), testing strategy,
   AGENTS and `.agents/skills/api-test-strategy/SKILL.md`. Keep exact past validation
   records. Repo skill edits must be synced in git; no personal skill installation needed.
8. Run focused and full deterministic suites, 2-worker lab execution, lint/format,
   Markdown links, wheel/sdist build and installed-wheel probe. Execute actual
   PostgreSQL/SMTP/container checks in GitHub Actions; resolve failures, then record
   actual results. Do not substitute local SQLite or fake delivery for those claims.
9. Publish finished Phase 5 on main with non-force Git update preserving current
   upstream changes, verify CI, publish evidence docs, and give an accurate final answer.

## Retrieval / publication

Repository: Pranay2444/playwright-python-enterprise-api-framework.
Phase 4 main head at checkpoint start: 5088401652247ad8b2548c37e25eec6f875d2a78.
The GitHub plugin supports fetch, create_tree, create_commit, create_branch and
update_ref; use these if terminal git authentication is unavailable. Public git
fetch works. Inspect the current branch/head before modifying or publishing.
Read AGENTS, the API testing skill, README and validation records before resuming.
Network dependency installation works via uv; no browser is needed for git-data
publication. Workflow dispatch was previously a browser-only operation, while
push/PR workflow runs, job logs and artifacts are accessible through GitHub tools.

Five private ReqRes project live tests from Phase 4 remain unexecuted because no
user key/project config is available. Preserve that limitation; never invent keys.
