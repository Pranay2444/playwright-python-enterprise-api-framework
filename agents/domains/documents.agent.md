# Documents domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/phase-5-test-plan.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Identify upload, metadata, download, delete, or idempotency operation. Record returned UUID, status and safe correlation ID.
2. Compare filename, MIME, size and checksum policy; keep the actual document bytes out of reports.
3. Check owner AND tenant predicates. Another user receives404, including within the same tenant; member/admin gate is a separate policy.
4. Inspect the test-owned row with a separate probe. Exact idempotent replay returns200; changed name/MIME/checksum returns409.
5. Preserve cleanup errors separately. Never search for and delete another user’s document to clear a failure.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
