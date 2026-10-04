# Owned disposable lab infrastructure

Read the [setup walkthrough](../docs/phase-5-walkthrough.md) before starting Compose.
Generate the ignored private signing file with `python scripts/init_lab.py`.
The root [compose.yaml](../compose.yaml) wires PostgreSQL, Mailpit, and the installed
FastAPI application. Ports bind to host loopback. Read the
[auth guide](../docs/phase-5-auth.md) for key handling and root bootstrap followed
by UID/GID10001 application execution. No real mail relay or SMS gateway exists.

The Python/PostgreSQL base tags are mutable; Mailpit is release-pinned, not
digest-pinned. The development lock is shared by the app image and tests. This is
a readable portfolio environment, not a production identity deployment.

`docker compose down` retains the DB volume. `down --volumes` intentionally deletes
this disposable stack's database and is used only for CI's own job. Accounts and
audit history have no public cleanup API; per-test PostgreSQL schemas are separately
owned and dropped by fixtures. Never commit `lab/.secrets` or a local database.
