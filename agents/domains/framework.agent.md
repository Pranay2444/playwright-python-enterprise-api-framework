# Framework domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/phase-5-workflow.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Identify setup/call/teardown, transport, fixture, package, receipt, Docker or CI failure. Preserve the original assertion separately from artifact errors.
2. Trace fixture resource ownership and request options, using safe method/path/status only; contexts and auth state belong to one test.
3. Check installed package origin and schema assets outside src. For Compose, verify DB/Mailpit/app health and application UID without dumping environments.
4. Check worker-isolated schemas/ports and driver ownership. Each concurrency thread must create its own Playwright driver.
5. An unavailable report directory adds a safe section; it must not produce INTERNALERROR or change the original test outcome.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
