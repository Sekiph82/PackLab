# PL-0074 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent finding

Exposure adapter now requires the selected coordinator and AcceptedPhotoMetadataFactory can bind actual exposure readings. No production path connects physical exposure adapter output to CaptureRuntimeViewModel controls and accepted-photo persistence, and tests do not exercise wrong-device rejection or the production adapter-to-metadata path. The integration criterion remains unmet.

Builder log format and protected-file handling are otherwise consistent with the batch handoff. Native Xcode/iPhone success is not inferred from Windows validation.

## Required remediation

Close the remaining production-seam and behavior-test gap described above without regressing the already-correct Batch-003 work. Tests must exercise the actual integrated adapter/bridge boundary required by the frozen criteria, not only a neighboring pure helper.

PL-0074 remains unchecked.

Decision: **CHANGES_REQUIRED**
