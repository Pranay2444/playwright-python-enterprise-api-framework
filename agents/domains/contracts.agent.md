# Contracts domain triage / RCA

Read [project instructions](../../AGENTS.md), [defect management](../../docs/defect-management.md),
and [the relevant policy](../../docs/contracts.md) before investigation. This guide does not
launch agents or authorize publishing issues/messages.

1. Separate HTTP status/media envelope, JSON Schema, Pydantic input/view and business relationship failures.
2. Use the safe schema location/rule, never jsonschema error message/instance or Pydantic input values.
3. Identify owned-app OpenAPI versus checked-in public partial contract. Generated schema agreement does not independently prove the app generator.
4. Compare acceptance basis before changing a required field/type/status. Allow additive public response fields and bypass valid factories for server negatives.
5. Retain a malformed-response regression and packaging probe so a missing asset cannot look like provider drift.

State observations, hypotheses and a discriminating check separately. Mark RCA
confirmed only when the causal mechanism is supported. Use the
[defect template](../../docs/templates/defect-report.md) and
[RCA worksheet](../../docs/templates/root-cause-analysis.md), add a meaningful
regression, and record target-specific retest results and residual uncertainty.
