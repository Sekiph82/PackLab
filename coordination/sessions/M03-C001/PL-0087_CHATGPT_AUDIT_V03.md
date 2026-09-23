# PL-0087 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent finding

NewScanWizard now uses NewScanWorkflowModel and ContentView creates and installs a real session from the produced draft. The required callback proof is still missing: tests call the workflow model directly and do not exercise the wizard/callback seam to prove exactly-one valid onStart, zero callbacks on invalid Start, and zero Start callbacks on Cancel.

The Batch-003 source changes are retained as valid progress; the task remains open only for the mandatory unresolved contract/integration evidence above.

## Required remediation

Add the missing authoritative cross-check or integrated behavior test at the actual production seam. Do not replace the current working implementation with another disconnected helper.

PL-0087 remains unchecked.

Decision: **CHANGES_REQUIRED**
