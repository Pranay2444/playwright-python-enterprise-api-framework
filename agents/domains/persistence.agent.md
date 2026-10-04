# Persistence domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/phase-5-workflow.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Record SQLite versus PostgreSQL, safe schema reference, transaction operation and returned IDs. A SQLite pass does not verify PostgreSQL locks.
2. Check schema ownership, foreign keys, unique constraints, commits/rollbacks and the separate probe connection.
3. Trace user-before-challenge locks, unused-row CAS and refresh session locks. Confirm a lock dependency before labeling a deadlock RCA.
4. For duplicate upload, check one document and one creation audit; verify rollback before reading the winner.
5. Teardown may drop only the random test-owned schema. Connection/setup failures are not automatically product defects.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
