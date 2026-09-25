# PL-0134 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

The previous static source-grep was replaced with a real executable HTTPS wire harness, which is a meaningful improvement. It uses the shared V1 golden create fixture, real /v1/pair and protected transfer routes, test TLS material, partial upload, receiver restart, status query, cancel/resume, completion, idempotent completion and exactly-once raw/report/index assertions. The isolated missing-declared-image fixture remains corrected.

The V03 requirement specifically calls for **sender same-ID restart/resume semantics and completion validation used by URLSessionTransferClient**. The harness writes a sender-state.json containing transfer ID/digest/receiver ID, but never reads that file after “restart”; it simply hard-codes "wire-transfer" in the resumed sender calls. Thus it does not test persisted sender restoration semantics at all.

It also accepts completion by asserting transfer_id + verified + state only; it does not apply the production Swift gate requiring matching digest + authenticated + terminal state. Certificate trust is exercised through the test CA, but the harness does not consume/compare the pairing-offer fingerprint as the Swift pinning client does.

Therefore the executable harness still proves receiver transport/ingest integration, not the full authoritative sender-state/completion contract requested by V03.

## Required remediation

Make the executable harness restore transfer identity from its persisted sender-state representation after constructing a fresh sender instance, derive the resumed transfer ID from that restored state rather than a hard-coded literal, compare package digest/receiver identity, and apply the same completion gate as production Swift: transfer ID + package digest + authenticated + verified + terminal state. Also explicitly verify the receiver certificate identity against the pairing-offer fingerprint in the harness.

PL-0134 remains unchecked.

Decision: **CHANGES_REQUIRED**
