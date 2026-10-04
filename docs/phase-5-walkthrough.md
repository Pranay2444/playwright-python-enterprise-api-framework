# Phase 5: run, explore, and maintain the owned lab

Use Python 3.11–3.13 (CI matrix), with Python 3.12 for the Docker app. No browser
binary is required: Playwright's API request driver sends HTTP directly. Docker
Desktop or Docker Engine with the Compose plugin is needed only for the real
PostgreSQL/SMTP/container checks. [Validation](validation.md) records actual runs.

## Fast local start

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m pytest -m "not external and not deployment"
python -m pytest tests/lab -n 2
```

The exact development lock includes the lab and test dependencies. For a consumer
install, `pip install '.[lab]'` selects optional app dependencies; base automation
does not require FastAPI. Dependency updates regenerate the lock using
`uv pip compile pyproject.toml --extra dev --extra lab -o requirements-dev.txt` and
repeat the matrix, wheel, and owned-stack checks. Review changes rather than
silently replacing pins.

Each lab test starts the actual app with a temporary SQLite file, captured email,
controlled clock, and real loopback HTTP requests. Public API doubles remain a
separate kind of test. Default collection skips external and deployment cases
unless opted in; explicit selectors keep counts clear. `.env` is needed for the
earlier public adapters, not the default owned fixture.

## Start the real disposable stack

```bash
python scripts/init_lab.py
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
```

The initializer never prints or overwrites the signing key. Its ignored file must
exist before Compose starts. Do not place a sample signing key in version control.
Read [the auth guide](phase-5-auth.md#secret-lifecycle-and-boundaries) for root
bootstrap followed by non-root application execution.

| Service | Host endpoint | Purpose |
| --- | --- | --- |
| App | `http://127.0.0.1:18080` | Installed FastAPI package; `/health`, `/docs`, `/openapi.json` |
| PostgreSQL | `127.0.0.1:5440` | Disposable `portfolio_lab` database |
| SMTP | `127.0.0.1:1025` | Mailpit capture; no real email relay |
| Mailpit UI/API | `http://127.0.0.1:8025` | Observe synthetic OTP emails |

Compose uses container DNS names `postgres` and `mailpit`. Host tests use the
loopback addresses above. PostgreSQL 17 and Python 3.12 base tags receive updates;
Mailpit is release-pinned to v1.31.4. Images are not digest-pinned. The app includes
the development lock for a simple shared lab image; this is not a minimal production
image. PostgreSQL readiness, upstream Mailpit readiness, and the app DB health
route govern startup. App readiness checks DB connectivity, not SMTP deliverability.

## PostgreSQL and real SMTP tests

Set only these disposable stack values, never user credentials:

```bash
export LAB_TEST_DATABASE_URL='postgresql+psycopg://lab:lab-disposable-password@127.0.0.1:5440/portfolio_lab'
export LAB_SMTP_HOST='127.0.0.1'
export LAB_SMTP_PORT='1025'
export LAB_MAILPIT_URL='http://127.0.0.1:8025'
python -m pytest tests/lab -n 2 --lab-postgres --lab-mailpit \
  --defect-dir=reports/defects --junitxml=reports/postgres-mailpit.xml
python -m pytest tests/deployment --lab-container \
  --defect-dir=reports/defects --junitxml=reports/container.xml
```

The first command runs per-test loopback application instances against real
PostgreSQL, with schema names `lab_test_<random UUID>` and real SMTP delivery.
It exercises row locking/CAS, uniqueness, persistence, and correlated email
retrieval while workers share only the infrastructure. Each schema is dropped in
fixture teardown, including application setup failure. The app container uses the
public schema separately; tests do not drop its schema.

The second command exercises the running installed app container without DB/clock
injection. It registers a synthetic email user, completes MFA, checks identity,
uploads/downloads/checks checksum, deletes/verifies absence, rotates refresh, and
logs out. A usable document ID is tracked for `finally` cleanup. Synthetic accounts
and audit rows remain in the development stack: there is no account-delete endpoint.
CI removes that job's entire disposable volume. No real SMS is sent in either run.

## Stop and reset deliberately

```bash
docker compose down
```

This stops services and retains the database volume/signing file for development.
For a **disposable stack whose data you intend to remove**, use
`docker compose down --volumes`. It permanently removes that Compose database
volume; it does not delete the host signing file. Never apply that cleanup command
to an unrelated stack. A clean DB reset removes users/documents/audits/refresh
history. Mailpit messages are ephemeral in this configuration.

## Configuration and direct app use

`LabSettings.from_env` requires `LAB_DATABASE_URL` and either `LAB_SIGNING_KEY`
or `LAB_SIGNING_KEY_FILE`. A supplied key value takes precedence over the file.
SMTP host/port are optional. The app does not implicitly discover a `.env` file.
The test fixture passes a `LabSettings` instance directly and generates a unique
key in memory. Lifetime/attempt/upload policies are explicit constructor fields;
they are not currently general environment-variable options.

For direct local Uvicorn, use a disposable SQLite database and the initialized file:

```bash
export LAB_DATABASE_URL='sqlite:///./lab/local.db'
export LAB_SIGNING_KEY_FILE='./lab/.secrets/signing-key'
python -m uvicorn framework_lab.app:create_app --factory --host 127.0.0.1 --port 18080 --no-access-log
```

Email login needs the SMTP service running. Prefer the Compose walkthrough for
the complete manual flow. Explore Swagger with synthetic `@example.test` data;
tokens and enrollment secrets must not be pasted into portfolio screenshots/issues.

## Recommended reading and practice

1. Read [workflow and patterns](phase-5-workflow.md), then `app.py` and `settings.py`.
2. Trace `AuthService.login/verify/refresh` beside [auth state](phase-5-auth.md).
3. Open `LabSession` and the lab clients; observe how raw HTTP errors remain testable.
4. Read `test_authentication.py` with the controlled clock. Advance time in tests,
   rather than adding 120-second sleeps.
5. Trace `test_upload_metadata_download_delete_and_database` into DocumentService.
   Change only one synthetic input and check API state and independent DB observation.
6. Inspect race tests and the PostgreSQL schema fixture before increasing workers.
7. Use [domain triage](defect-management.md) on an intentionally failed owned case;
   classify it before editing an expectation.

Useful commands:

```bash
python -m pytest tests/lab/test_authentication.py -q
python -m pytest tests/lab/test_concurrency.py -q
python -m pytest tests/lab/test_documents.py -q
python -m pytest -m 'security and not external and not deployment'
ruff check .
ruff format --check .
python -m build
python scripts/check_wheel.py
python scripts/check_docs.py
```

Generated-input checks are bounded Hypothesis examples against owned policy, not
unrestricted public fuzzing. Selected app response schemas are validated against
its OpenAPI; that does not prove full OpenAPI conformance or an external contract.

## Troubleshooting by layer

| Symptom | First useful check | Domain |
| --- | --- | --- |
| Compose missing secret file | Run initializer; verify existence/permissions without reading value | Framework |
| Port already allocated | Stop this owned stack or use a separate deliberate port mapping | Framework |
| PostgreSQL unavailable | Compose health and loopback DB config; separate connection error from HTTP | Persistence |
| SMTP 503 / code timeout | SMTP reachability and exact recipient/challenge correlation; no latest-mail shortcut | Authentication |
| Correct TOTP rejected | Injected time/current step, prior accepted step, current challenge | Authentication |
| Refresh winner subsequently gets 401 | Check known-token reuse/family revocation; concurrent refresh is rejected | Authentication |
| Duplicate upload conflict | Compare idempotency key, filename, MIME, bytes/checksum | Documents |
| Contract assertion fails | Safe schema location plus project rule; keep bad values private | Contracts |
| Test failed but receipt missing | Read redacted receipt warning; check writable reports path | Framework |

CI runs three Python quality jobs, then real PostgreSQL/Mailpit parallel tests and
container smoke. It uploads JUnit/receipts for seven days and always shuts down
its disposable stack. Live provider jobs remain manually opted in. Follow
[validation.md](validation.md) for run-specific outcomes; a workflow definition
alone is not execution evidence or repository branch protection.
