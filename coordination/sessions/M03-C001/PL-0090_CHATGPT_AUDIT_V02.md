# PL-0090 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `58acf734614c3fb7f16b071bda8810f7c6fd9dce`
Remediation log: `PL-0090_CODEX_LOG_V02.md`

## Independent result

The remediation adds real launch-time discovery and a visible Resume/Discard/blocked UI. Persisted accepted/rejected/replacement/epoch fields are also carried forward.

The actual resume/discard behavior is still incomplete.

### Resume and Discard callbacks are no-ops at app level

`ContentView` presents `SessionResumeView`, but:
- `onResume` only sets `showResume = false`;
- `onDiscard` only sets `showResume = false`.

No resumable session is installed into the active app/session model, and discard does not remove/quarantine the session.

### Discovery bypasses the crash-recovery reopen path

`SessionDiscoveryService.discover()` directly reads metadata/state/images. It does not call `ScanSessionStore.reopen()`, so stale-temp recovery and transaction validation are bypassed during the actual launch discovery path.

It also does not validate per-photo record files, so a session with valid state/source names but corrupt/missing records can be offered as resumable.

### Frozen restart/failure tests remain incomplete

The new test covers one clean discovered session. It does not cover:
- stale temp during actual discovery;
- simulated partial/crash state;
- missing per-photo record;
- corrupt record;
- version mismatch through discovery;
- real discard behavior.

## Required remediation

1. Make discovery/resume use the same authoritative reopen/recovery validator as PL-0088.
2. Reconstruct and install a real active session object on Resume.
3. Make Discard perform a defined safe delete/quarantine path.
4. Validate metadata/state/per-photo/source records together before offering Resume.
5. Add restart tests for clean, partial/crash, stale-temp, missing/corrupt record/source and version mismatch.

PL-0090 remains unchecked.

Decision: **CHANGES_REQUIRED**
