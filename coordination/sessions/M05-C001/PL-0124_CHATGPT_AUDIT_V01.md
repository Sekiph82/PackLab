# PL-0124 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

Receiver-side resumability is substantially implemented: .part + atomic checkpoint state, deterministic next offset, duplicate-chunk idempotency, out-of-order/conflict rejection, cancel/resume, receiver restart, and multi-chunk verification all have filesystem tests.

The frozen task still requires sender-side reconnect/restart behavior at the production transfer seam. The iOS app has no network transfer client that queries receiver status after reconnect/restart and resumes from the authoritative offset. TransferViewModel can consume a status object, but nothing actually fetches that status over the network or resumes chunk upload from it. There are also no Swift tests proving sender restart/reconnect against the real protocol service.

## Required remediation

Preserve ResumableTransferStore. Implement the production iOS transfer client/status query/resume path, persist enough non-secret sender transfer identity to reconnect, and add integrated sender+receiver restart/reconnect tests proving resume from confirmed offset rather than blind restart.

PL-0124 remains unchecked.

Decision: **CHANGES_REQUIRED**
