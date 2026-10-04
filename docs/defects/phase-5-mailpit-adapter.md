# Phase 5 Mailpit adapter failure and RCA

- **Domain / service / target:** Authentication; lab; PostgreSQL and real SMTP/Mailpit.
- **Classification:** Framework integration adapter.
- **Source commit:** `e80a97d` (initial Phase 5 source).
- **Observed:** 4 October 2026, first [owned CI run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37218454842).
- **Actual:** Three Python quality jobs passed. Docker startup/app UID check passed.
  Owned integration reported **31 failed, 19 passed**. Container smoke did not run
  because the preceding integration step failed. Artifact upload and stack shutdown ran.
- **Expected:** Read the exact recipient/challenge email and complete verification.
- **Confirmed evidence:** Direct code-reader cases failed in `UUID(message["ID"])`.
  Mailpit v1.31.4's [source](https://github.com/axllent/mailpit/blob/v1.31.4/internal/shortuuid/shortuuid.go)
  generates opaque 22-character base62 IDs. The adapter incorrectly assumed UUID text.
- **RCA:** Confirmed identifier-format mismatch in the automation reader. It failed
  before requesting the message body, preventing email-MFA completion. This was not
  evidence of a password/JWT/database policy defect. Fail-closed LabSession masked
  underlying details in its public error, while direct reader regressions located the cause.
- **Corrective action:** Validate 22-character ASCII alphanumeric message IDs,
  preserve case/value, and reject unsafe path characters. Challenge IDs remain UUIDs.
- **Additional unit finding:** An SMTP-style CRLF body reproduced a separate parser
  rejection (1 failed/3 passed before the fix). Normalize CRLF to LF before strict
  challenge/code matching. That unit reproduction does not establish which newline
  format the first CI message body used, because its ID error prevented retrieval.
- **Regression:** Both LF/CRLF bodies, a matching subject/recipient with wrong body
  challenge, non-hex base62 IDs, and unsafe ID length/query/traversal/Unicode rejection.
  Large synthetic upload parameters now have static test IDs to keep logs/JUnit small.
- **Retest status:** Local focused/full/package and subsequent real CI outcomes are
  recorded in [validation.md](../validation.md). Treat only the successful executed
  run as closure evidence; the failed run remains linked for causal history.
- **Impact / priority:** Blocked owned email integration validation and release gate.
  No production incident or real recipient impact is claimed.

This is a checked-in redacted report, not a published GitHub issue or message.
No OTP, token, email body or raw environment data is included.
