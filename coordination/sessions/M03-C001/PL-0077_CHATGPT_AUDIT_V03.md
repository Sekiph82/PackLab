# PL-0077 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent finding

CameraRecoveryOwner now has restart and cancellation hooks, but the real preview path never assigns onStateChange into the app view model/UI, and the still adapter's bind(to:) is not shown in production composition. Recovery state/messages therefore remain partly disconnected from the app, and tests still exercise the pure recovery model rather than the integrated notification→cancel/restart/UI seam.

Builder log formatting and protected-file handling are otherwise consistent. Windows regression evidence is retained, but native-device behavior is not assumed.

## Required remediation

Close the exact remaining production integration/test boundary above while preserving all accepted Batch-003 work. The repaired path must be exercised by behavior-bearing tests at the actual service/adapter seam.

PL-0077 remains unchecked.

Decision: **CHANGES_REQUIRED**
