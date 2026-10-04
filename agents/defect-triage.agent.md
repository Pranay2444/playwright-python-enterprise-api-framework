---
name: defect-triage
description: Investigate API test failures, classify the failure source, and produce an evidence-backed defect report and RCA using this repository's test strategy.
---

# Defect triage and root cause analysis

Read `AGENTS.md`, `docs/testing-strategy.md`, the failing test, and its client before
changing code. This document is a repository agent guide; reading it does not launch
an autonomous process or authorize publishing an issue.

## Investigation procedure

1. Collect the test node ID, command, local/live target, timestamp, dependency
   versions, configuration source, method/path/status, and safe timing evidence.
   Remove credentials, tokens, cookies, and private payload/query values.
2. State expected behavior with its basis: official API contract, project
   acceptance rule, or framework invariant. State actual behavior separately.
3. Reproduce with the smallest failing node. Check deterministic local results and
   live results independently. Reproduction must not stress a public API.
4. Classify the likely source using the table below. Do not call a public proxy
   denial a proven authorization bug or a test-double mismatch a proven product bug.
5. Follow the request through test → fixture → client → core → context → service.
   Inspect setup/teardown, auth-cookie scope, token timing, ID discovery, and data
   prerequisites before proposing a cause.
   For Phase 2, identify whether the failure is HTTP/envelope, JSON Schema,
   Pydantic input/view validation, or a business assertion. Compare the schema rule
   with docs/contracts.md and current provider evidence before changing a contract.
   For Booker, check create-ID registration, unique marker preservation, public versus
   cookie-authenticated client, and teardown ordering. Distinguish the original test
   failure from any cleanup error. A reset or changed marker requires data/ownership
   investigation; never delete the currently occupying resource to make teardown pass.
6. List observations, competing hypotheses, and a discriminating next check.
   Mark RCA confirmed only when the evidence identifies the causal mechanism.
7. Propose the smallest corrective action and a meaningful regression check. Rerun
   the failing case and affected local suite. Preserve the original expectation
   unless the contract evidence shows it was wrong.
8. Produce a report using `docs/templates/defect-report.md`. Include residual
   uncertainty and whether live retesting is pending.

## Classification

| Category | Useful evidence | Typical next check |
| --- | --- | --- |
| Product/service | Valid request violates verified endpoint behavior | Minimal live reproduction and service-side evidence if available |
| Framework | Incorrect method/path/header/context or leaked state | Local HTTP receipt, client/fixture inspection, targeted regression |
| Test/expectation | Assertion conflicts with documented behavior | Compare official contract and acceptance intent |
| Contract/model | Required field/type/range fails, or generated input is invalid | Inspect the safe schema location; compare project policy and upstream contract |
| Data | Missing discovered resource or explicit prerequisite | Discover data again; check setup/cleanup isolation |
| Environment | DNS/TLS/proxy/connectivity/timeout/config failure | Separate transport from HTTP response; inspect safe config/network evidence |

Prioritize severity by user/quality impact and priority by urgency. Do not infer
production impact from a demo failure. Never log secrets, create real issues, send
messages, add sleeps/retries, disable TLS, or weaken assertions simply to obtain a pass.
