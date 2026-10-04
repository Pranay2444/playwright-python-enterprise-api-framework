# Domain-based defect evidence, triage, and RCA

The project has an opt-in Pytest failure receipt mechanism, domain investigation
guides, a [defect template](templates/defect-report.md), an
[RCA worksheet](templates/root-cause-analysis.md), and a GitHub issue form.
These are local reporting aids. They do not open issues, assign people, send
messages, or automatically declare an application defect.

## Routing is separate from classification

| Domain | Investigate first | Guide |
| --- | --- | --- |
| Authentication | Password/MFA, identity, claims, expiry, replay, delivery, logout | [Authentication](../agents/domains/authentication.agent.md) |
| Documents | Filename/MIME/size, upload/download, ownership, idempotency | [Documents](../agents/domains/documents.agent.md) |
| Persistence | Rows/constraints/transactions, locking, schemas, audit | [Persistence](../agents/domains/persistence.agent.md) |
| Contracts | HTTP envelope, selected JSON schema, strict models and expectation basis | [Contracts](../agents/domains/contracts.agent.md) |
| Framework | Fixtures, clients, transport, packaging, reporting, Compose/CI | [Framework](../agents/domains/framework.agent.md) |
| Public APIs | DummyJSON/Booker/ReqRes target behavior and owned-resource cleanup | [Public APIs](../agents/domains/public-apis.agent.md) |

A persistence-domain failure can be an environment problem, a test expectation,
or an app transaction defect. Domain identifies the investigation area;
classification identifies the supported cause. Severity describes concrete impact;
priority describes urgency. A demo failure does not establish production impact.

## Generate receipts

```bash
python -m pytest tests/lab --defect-dir=reports/defects
python -m pytest tests/lab -n 2 --defect-dir=reports/defects
```

`tests/conftest.py` loads the plugin. It writes only failed setup/call/teardown
reports, under `reports/defects/<random run>/<main or gwN>/<domain>/` with a random
evidence filename. Each worker may have its own run UUID. There is no central
aggregation database; collect the directory/artifact tree by commit and CI run.
The `domain` marker is allowlisted; unknown values fall back to framework.
Provider suite directories default to public-apis; explicit markers take precedence.

| Receipt field | Meaning |
| --- | --- |
| `schema_version` | Current shape version 1 |
| `case` / `case_hash` | Sanitized parameter-free node and hash of that node only |
| `evidence_id` | Random unique evidence identifier; avoids parameter-case overwrites |
| `domain` | One of six routing domains |
| `service` | Lab, DummyJSON, Booker, ReqRes, or framework |
| `target` | SQLite/PostgreSQL/container/local-http/public-api/local-check |
| `phase` | Setup, call, or teardown |
| `outcome` / `duration_seconds` / `observed_at` | Failure, safe timing, UTC timestamp |
| `classification` / `rca_status` | Initially untriaged / unknown |

Parameter suffixes are **discarded before hashing**. Hashing a six-digit OTP would
allow offline enumeration, so the plugin does not retain even that parameter hash.
It does not copy tracebacks, exception strings, response bodies, headers, tokens,
emails, or arbitrary user fields. Files are mode0600 on supporting systems.
Use static test names; secrets must never be embedded in filenames/function names.
An unwritable report directory adds a safe report section and retains the original
failure, instead of crashing Pytest internally. No receipt means no evidence of a
pass; check the actual Pytest/JUnit outcome.

JUnit is separate and may contain assertion/traceback text. `junit_logging=no`
prevents log capture in that artifact, but does not scrub every custom assertion.
Review JUnit, terminal output, and manually collected evidence before public sharing.
Do not enable `--showlocals`, dump mail/token responses, or attach raw environments.
CI retains artifacts for seven days; this is not a durable incident archive.

## Investigation workflow

1. Record commit, command, target/service, UTC time, Python/dependency pins, safe
   method/path/status, correlation ID and failure phase. Preserve the original failure.
2. State expected behavior with its source: owned policy, verified provider contract,
   framework invariant, or generator rule. A generated-input rule is not automatically
   a provider rejection contract.
3. Reproduce the smallest node on the same target. A SQLite pass cannot clear a
   PostgreSQL lock failure. A local model pass cannot clear a public compatibility failure.
4. Route to the domain guide; trace fixture → client → transport → route → service
   → database/delivery. Check setup and teardown separately from the main assertion.
5. List observations and competing hypotheses. Choose one bounded discriminating
   check, such as affected session state or one SQL constraint result, avoiding secrets.
6. Classify product/app, framework, expectation/contract, data, or environment only
   as supported. Keep RCA unknown/suspected until a mechanism is demonstrated.
7. Fix that mechanism with a small change and a regression that would have caught
   it. Rerun the affected target, adjacent invariants, and required release gates.
8. Write retest results and residual uncertainty using the templates. Update
   validation evidence. Human review determines whether an issue should be published;
   this phase never publishes one automatically.

## Evidence examples and causal limits

- **Observation:** refresh race returns200/401 and the winning access later401.
  **Policy explanation:** used-token detection revokes the family. This is expected,
  unless the test's intended refresh sequence was serialized and a different mechanism
  is demonstrated. Do not add request retries.
- **Observation:** PostgreSQL detects a deadlock during overlapping login/verify.
  **Hypothesis:** inconsistent lock order. Confirm with the relevant transactions and
  dependency cycle before changing order; retain a bounded race regression.
- **Observation:** Mailpit timeout. **Alternatives:** SMTP failure, recipient/subject
  mismatch, or infrastructure unavailable. A timeout alone proves none of them.
- **Observation:** upload HTTP201 but separate DB row missing. Check schema/transaction
  and returned ID, rather than assuming the response validator proves persistence.

The top-level [triage agent guide](../agents/defect-triage.agent.md) retains the
earlier provider rules. Domain `.agent.md` files are instructions a human or coding
assistant can follow; they do not launch background agents or expand publication authority.
