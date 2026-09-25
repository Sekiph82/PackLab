# PL-0122 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

Manual pairing is now functional: the UI accepts host/port/receiver ID/pairing ID/fingerprint/code directly when no PairingOffer is pre-injected, reconnect persistence excludes the one-time code, and the production preview controller installs real stop/restore handlers into ProductionCaptureCameraLifecycle. Scanner presentation is gated on beginQRScan(), so it is no longer shown before acquisition succeeds.

Two frozen evidence/runtime gaps remain.

First, the required Swift pairing matrix still has **no wrong-version PairingOffer test**. PairingOffer(data:) contains the guard, but V03 requires the behavior test.

Second, ProductionCaptureCameraLifecycle.stopAndReleaseForPairing() returns false whenever its preview stop handler is absent. The Send-to-PackLab workflow is launched from Scan History presented as a sheet over ContentView. If the production preview controller has already disappeared/cleared its handler, the camera is already released, but QR pairing is incorrectly treated as “Production camera is still in use” and cannot start. The lifecycle bridge has no explicit already-released/idle state to distinguish “nothing to stop” from “failed to stop.” The fake lifecycle test cannot expose this production state.

## Required remediation

Add an explicit production camera lifecycle state so QR acquisition succeeds when the capture camera is already safely released, while still failing when an active camera cannot be stopped. Add tests for active-stop success, active-stop refusal, already-idle/released success, hand-back only when needed, and PairingOffer wrong-version rejection.

PL-0122 remains unchecked.

Decision: **CHANGES_REQUIRED**
