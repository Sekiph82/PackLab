# PL-0121 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

The shared fixture is now bundled into the Swift test target, and Swift genuinely decodes/encodes create, chunk, status, cancel, resume, completion and error objects from the same golden JSON used by Python. That closes the main fixture-authority gap.

The fail-closed Swift decoder test is still incorrect/incomplete. It builds three malformed values for status, completion and error, but then decodes **all three as TransferStatusMessage**. Therefore completion and error model version/protocol rejection are not actually exercised. No unsupported-version/protocol test is present for TransferControlMessage either.

The frozen V03 criterion explicitly requires fail-closed validation for status/completion/error/control as applicable with stable mapping.

## Required remediation

Fix the Swift negative matrix so each malformed golden-derived object is decoded with its own production type: TransferStatusMessage, TransferCompletionAcknowledgement, TransferErrorEnvelope and TransferControlMessage. Cover wrong protocol name and unsupported version for each applicable model, and assert the expected stable TransferWireError outcome.

PL-0121 remains unchecked.

Decision: **CHANGES_REQUIRED**
