# PL-0078 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `ece1d7bb05a9cce0f9248ce80ba576d91b77775a`

## Independent result

The remediation successfully adds:
- a real physical provider reading ProcessInfo thermal state;
- important-volume available capacity;
- UIDevice battery state/level;
- a truthful unavailable provider;
- an actor-isolated periodic monitor abstraction;
- preflight evaluation;
- a final-main SwiftUI health warning message.

Two mandatory behaviors remain incomplete.

### 1. Periodic active-session monitoring is not actually started

Final `ContentView.CaptureRuntimeViewModel.start()` calls:

`health = await healthMonitor.preflight()`

but never calls `healthMonitor.start(...)`.

Therefore the app takes one health snapshot at startup and does not update thermal/storage/battery health during a long active capture session.

The periodic monitor implementation exists only as an unused seam.

### 2. Hard-stop is not bound to real capture/session admission

The UI displays the messages for both `.warning` and `.hardStop`.

No inspected capture button/still-capture/session path checks `health.allowsCapture` before accepting/requesting a still, and no hard-stop transition stops/blocks an active capture session.

Thus `.hardStop` is currently informational, not fail-safe session control.

### 3. Tests do not cover provider/preflight/live update integration

The new test covers only pure gate mapping. It does not test:
- injected provider snapshot mapping;
- monitor preflight;
- periodic live updates;
- start/stop idempotency;
- a transition into hard stop while active;
- capture admission being blocked.

## Criteria

- PASS: 1-11, 15-18
- FAIL: 12, 13, 14, 19

## Required remediation

1. Start/stop the health monitor with the real active capture lifecycle and publish periodic updates into the runtime view model.
2. Enforce `hardStop` at the actual still/session admission boundary.
3. Keep warnings visible while allowing capture, but block capture on hard-stop states.
4. Add injected-provider tests for preflight, live update, monitor stop/idempotency and hard-stop capture blocking.

PL-0078 remains unchecked.

Decision: **CHANGES_REQUIRED**
