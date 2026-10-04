# Root cause analysis worksheet

- **Reference / domain / service / execution target:**
- **Commit, test node without parameters, command, UTC timestamp:**
- **Expected invariant and its source:**
- **Observed failure and safe correlation/evidence IDs:**
- **Impact / severity / priority basis:**
- **Timeline:** Events and state transitions, without secrets or raw mail/body data
- **Confirmed observations:** Only what the evidence shows
- **Competing hypotheses:** Include framework, expectation, data, environment
- **Discriminating check and result:** Smallest check separating those hypotheses
- **RCA status:** Unknown / suspected / confirmed
- **Causal mechanism:** Explain the transaction/state/transport sequence when confirmed
- **Contributing conditions:** Separate from the direct cause
- **Corrective action:** Specific implementation or expectation change, with basis
- **Regression:** Test and invariant that failed before the fix
- **Retest:** Command, target, commit, outcome, CI link
- **Residual uncertainty / pending account or infrastructure verification:**
- **Prevention / documentation change:** Only if justified by the mechanism

Do not equate the domain receipt with confirmed causation. Remove credentials,
OTP/TOTP secrets, token values, document contents and private parameter values.
