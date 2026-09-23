# PL-0093 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `13077857cc56af60fc8ae1656281099c9c24bf06`
Remediation log: `PL-0093_CODEX_LOG_V02.md`

## Independent result

The remediation improves deletion substantially:
- candidate-bound plans exist;
- session ID/path checks are stronger;
- the UI names the exact session and requires destructive confirmation;
- deletion reports were introduced;
- normal deletion and traversal behavior have filesystem coverage.

Mandatory safety boundaries remain open.

### Non-authoritative in-root plans can still delete data

`SessionDeletionPlan(root:session:)` remains public and creates `authoritative = false`.

`validate` does not require `authoritative == true`, and `SafeSessionDeleter.deleteDetailed` accepts that plan. Therefore an arbitrary syntactically valid in-root directory can still be deleted without proving it came from an authoritative session/history candidate.

This directly violates the remediation requirement to bind deletion to a validated canonical PackLab session/history identity.

### History cleanup is optional and the real UI does not request it

`deleteDetailed(..., historyIndex: URL? = nil)` only cleans an external history index when a caller supplies one. `SessionDeletionView` calls the default nil form. If authoritative external history/index state exists, the real UI path does not coordinate its cleanup.

### Partial-failure diagnostics are not retained

The method builds a `DeletionReport`, but if any failure exists it throws `.partialFailure` instead of returning/persisting the detailed failed paths. The UI reduces this to a generic message, so the promised detailed recoverable diagnostics are not available after failure.

### Frozen destructive-boundary tests are incomplete

The criteria require filesystem tests for:
- success;
- cancellation;
- missing session;
- injected partial failure;
- path traversal;
- symlink escape.

The current tests do not exercise injected partial failure or a real symlink escape, and do not prove non-authoritative plans are rejected.

## Required remediation

1. Make destructive execution require an authoritative candidate/session identity and reject `authoritative == false` plans.
2. Coordinate all authoritative history/index cleanup in the real UI deletion path.
3. Preserve/report detailed partial-failure paths instead of collapsing them to an opaque error.
4. Add tests for non-authoritative rejection, missing session, injected partial failure and symlink escape in addition to success/cancel/traversal.

PL-0093 remains unchecked.

Decision: **CHANGES_REQUIRED**
