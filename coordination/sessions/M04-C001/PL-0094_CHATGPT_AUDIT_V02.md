# PL-0094 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

The remediation closes the two major Batch-001 findings:
- the sharpness reason-code interpolation is fixed and now produces stable values such as `sharpness_accept`, `sharpness_warn`, and `sharpness_reject`;
- `SharpnessAnalyzer` is composed into the production-used `M04CandidateQualityRuntime`, and the active preset's sharpness policy propagates into `CandidateQualityMetrics`.

Provisional calibration remains truthfully labelled and no physical iPhone calibration is claimed.

One frozen V02 criterion is still not fully evidenced.

### Missing required frame-level warn/reject and exact-boundary behavior tests

The V02 criteria explicitly require deterministic tests for:
- a sharp frame;
- a mildly blurred / WARN frame;
- a strongly blurred / REJECT frame;
- unavailable input;
- exact ACCEPT and WARN threshold boundaries;
- runtime propagation.

The final test target proves sharp/unavailable behavior, runtime reason-code propagation, and threshold object values/calibration truthfulness, but it does not drive `SharpnessAnalyzer.analyze` with concrete candidate frames that deterministically land in the WARN and REJECT bands, nor does it prove exact analyzer equality behavior at both boundaries.

The implementation itself is materially improved and should be preserved.

## Required remediation

Add deterministic frame/fixture tests (or a production-used injectable metric-input seam) that prove `SharpnessAnalyzer` produces WARN and REJECT bands and verify equality at `acceptMinimum` and `warnMinimum`. Preserve the current production runtime integration and provisional calibration contract.

PL-0094 remains unchecked.

Decision: **CHANGES_REQUIRED**
