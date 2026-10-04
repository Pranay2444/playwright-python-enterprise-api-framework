# Authentication domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/phase-5-auth.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Identify password, delivery, verification, JWT, refresh, or logout transition; compare the expected state and status.
2. Check server clock and client deadline separately. Inspect challenge expiry/attempts/consumption and session revocation without reading code/token values.
3. For email, check exact recipient plus challenge subject/body correlation. For TOTP, check current step and persisted last step; do not relax the window to obtain a pass.
4. For refresh, distinguish unknown digest from known used history. Concurrent reuse revokes the family by policy; never add automatic refresh/request replay.
5. Reproduce with the bounded owned HTTP/concurrency test. A provider token manager has different semantics and cannot substitute for this lab.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
