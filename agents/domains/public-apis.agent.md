# Public APIs domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/phase-4-test-plan.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Identify DummyJSON, Booker or ReqRes demo/project, and local model versus live target. Consult that phase’s acceptance basis.
2. Keep Bearer tokens, Booker cookies and ReqRes per-request API keys separate. Missing private project config is setup evidence, not a live pass.
3. DummyJSON cart and ReqRes demo writes are simulated. Booker/shared resets and ReqRes soft deletion limit persistence claims.
4. For owned persistent resources, register usable IDs early, preserve synthetic markers, verify ownership before cleanup and GET absence afterward.
5. Keep429/Retry-After visible. Do not exhaust quotas, retry to mask failures, mutate seed data, substitute tutorial keys or infer authorization causes from one403.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
