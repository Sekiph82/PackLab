# PL-0093 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `dab847141c4fb5496e93e227e81c10e8b5a03971`

## Independent findings

The child adds useful destructive-operation guards:
- explicit confirmation boolean;
- standardized/resolved root/session paths;
- root-self/outside-root rejection;
- symlink-escape rejection;
- actor-isolated deletion;
- partial-failure error instead of false success.

Mandatory ownership/UI/test protections remain incomplete.

### Confirmation does not identify the actual scan to the user

The API takes only `confirmed: Bool`. No SwiftUI confirmation flow presents the specific scan/session identity before deletion. Criterion 10 / Requirement A is not implemented as a user workflow.

### Deletion target is not bound to an authoritative session/history record

`SessionDeletionPlan` accepts any URL under the supplied root. It does not require a validated session ID discovered from authoritative PackLab storage/history. A caller can therefore plan deletion of an arbitrary in-root directory that is not proven to be the selected PackLab session.

### Associated index/history cleanup is not coordinated

Removing the session directory may clean local files inside it, but there is no coordinated update/removal of authoritative history/index/finalization state if any such record exists outside that directory. Recoverable partial-failure diagnostics also carry no detail about what was/was not removed.

### Frozen filesystem tests are largely missing

Criterion 14 requires:
- normal deletion;
- cancellation;
- missing files;
- partial failure;
- malicious/out-of-root path attempts.

The inspected test covers confirmation rejection, one allowed in-root path, and one outside-root path only. It does not perform filesystem deletion, symlink attack, missing-file behavior or injected partial failure.

## Criteria

- PASS: 1-9, 16-18
- FAIL: 10, 11, 12, 13, 14, 15, 19-20

## Required remediation

1. Bind deletion to a validated canonical PackLab session/history identity, not an arbitrary in-root URL.
2. Add a real confirmation UI that clearly identifies the scan/session being destroyed.
3. Coordinate cleanup of session files, derivatives/temp data and authoritative history/index references.
4. Preserve detailed recoverable diagnostics for partial deletion failures.
5. Add temporary-filesystem tests for successful deletion, cancellation, already-missing session, partial/injected failure, traversal and symlink escape.
6. Publish a complete task-specific log checkpoint and stop before M04.

PL-0093 remains unchecked.

Decision: **CHANGES_REQUIRED**
