# PL-0087 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `181eb111af0cea4e4f1739133d9fbafc4fb29a85`
Remediation log: `PL-0087_CODEX_LOG_V02.md`

## Independent result

The remediation materially improves the New Scan flow:
- the wizard is reachable from the real root toolbar;
- invalid Start attempts now display a visible error;
- the accepted M02 mode IDs remain `freehand`, `guided_orbit`, and `turntable`;
- cancellation/start/failure state primitives were added.

One frozen requirement remains unmet.

### Behavior-bearing Start callback coverage is not implemented

`NewScanWorkflowModel` is tested, but that model is not used by `NewScanWizard`. The real view still owns its own validation and invokes the injected `onStart` closure directly.

The remediation criterion requires tests for the **successful Start callback** and invalid Start prevention on the actual workflow seam. The added test proves only that an independent model returns a draft and changes its own state; it does not prove that the real wizard invokes `onStart` exactly once for a valid draft and never invokes it for invalid input.

The root `ContentView` callback also currently discards the draft and only closes the sheet, so the app-level handoff remains unverified.

## Required remediation

1. Move the wizard behavior behind a testable view-model/workflow seam actually used by `NewScanWizard`, or otherwise add a testable callback adapter.
2. Prove valid Start invokes the supplied callback exactly once with the normalized draft.
3. Prove invalid Start does not invoke the callback and keeps visible validation state.
4. Preserve root reachability, cancellation behavior and all M02 capture-mode IDs.

PL-0087 remains unchecked.

Decision: **CHANGES_REQUIRED**
