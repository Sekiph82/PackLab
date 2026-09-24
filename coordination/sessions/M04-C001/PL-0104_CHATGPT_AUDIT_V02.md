# PL-0104 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

The remediation successfully composes `GuidedAutoCaptureService` into the production `CaptureRuntimeViewModel`, reuses the existing `AdmissionControlledStillCaptureService`, and persists accepted auto-captures through the canonical session transaction. Cooldown and accepted coverage update are also proven.

However, the frozen V02 gate matrix is incomplete.

### Missing required production-gate tests

The V02 work order requires integrated tests for:
- quality rejection;
- missing coverage target;
- pose ineligible;
- overlap blocked;
- health hard stop;
- in-flight duplicate suppression;
- cooldown boundary;
- rejected-candidate rearm;
- accepted capture.

The final tests cover accepted capture, in-flight suppression, cooldown, and pose ineligibility, but do not explicitly exercise the production runtime/service path for quality rejection, missing target, overlap blocked, health hard stop, and rejected-candidate rearm.

## Required remediation

Add integrated `CaptureRuntimeViewModel` / `GuidedAutoCaptureService` tests for the missing gate reasons and prove each one prevents the backend call when required, while rejected-candidate rearm restores eligibility without corrupting session state.

PL-0104 remains unchecked.

Decision: **CHANGES_REQUIRED**
