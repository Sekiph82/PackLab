# CLAUDE_PEER_REVIEW - PR #25 receiver auto-start when paired (V01)

Reviewer: independent Claude peer reviewer (did not author the change). Own findings only.
Head: origin/fix/receiver-autostart-paired 839b9adb; base origin/main 185c2dbf.
Diff: capture_inbox.py +14, shell.py +4, tests/studio/test_capture_inbox.py +33.

## Tests run (reviewer)
- Worktree C:\Users\sekip\Desktop\PackLab-wt-autostart, .venv python, QT_QPA_PLATFORM=offscreen:
  `pytest tests/studio/test_capture_inbox.py` -> 6 passed (pytest `pythonpath` resolves the worktree source).
- Probe (scratch script, QStandardPaths test mode, worktree source on sys.path): `StudioMainWindow()` with the
  default receiver factory + one `processEvents()` -> `<AppLocalData>/transfer-inbox` did not exist before, exists after.
  (Probe residue: C:\Users\sekip\AppData\Local\qttest\ - created by this probe, safe to delete; deletion was not permitted to the reviewer.)

## Findings

### MEDIUM-1 Auto-start runs in every StudioMainWindow, including build smoke and tests (shell.py:272-275)
`QTimer.singleShot(0, inbox_view.resume_for_paired_devices)` is unconditional. Before this PR the receiver
session was lazy (created only when the Capture Inbox page was shown). Now:
- Build smoke (`app.py` build_smoke branch, documented "must not create user projects or settings") calls
  `processEvents()`, so the default factory now creates `%LOCALAPPDATA%\PackLab\PackLab Studio\transfer-inbox`
  and `receiver-id` in the real user profile (reproduced via probe above).
- Many tests construct `StudioMainWindow()` without `receiver_session_factory` (e.g. tests/studio/test_jobs.py:41,
  test_m06_r01.py:29/94, test_labels_export_library.py:360/369). On the owner machine, where a phone IS paired,
  these tests would open a TLS listener on 0.0.0.0:8443 (or a random port if Studio holds 8443) from the
  pytest/build-smoke process using the real device store and TLS identity, and would touch the real TLS files.
Fix (small): opt in only from the real launch path, e.g. call `resume_for_paired_devices` from `app.run()`
non-smoke branch (or a constructor flag defaulting to False), plus a test that a default-constructed window
never invokes the factory.

### MEDIUM-2 Preferred-port fallback silently defeats the feature (receiver_session.py:97-102)
If 8443 is busy at launch the receiver binds a random port; the phone's stored pairing identity holds the old
host:port, so it stays at "Sending 0%" - the exact symptom this PR targets - and the only signal is the
status label on a page the owner is not looking at. Same for a DHCP LAN IP change. Not a security defect.
Recommend: on auto-start, if the bound port != preferred (or LAN host changed since pairing), surface a
status-bar/notification warning; or skip the random fallback in auto-start mode. Acceptable as a tracked follow-up.

### LOW-1 Auto-start issues and keeps rotating a pairing offer (capture_inbox.py:216-217, _tick)
`start_receiving()` always calls `new_code()`, so from launch a live one-time offer exists and is renewed every
120 s for the whole session, even though the user did not ask to pair. Code is 8 chars from 36 symbols
(~41 bits, `secrets.choice`), single-use, 120 s TTL, offer only visible on-screen, TLS-pinned; wrong codes are
not rate-limited but online brute force is infeasible. Risk is small, but least-exposure says auto-start
should listen for paired devices only and not issue an offer until the owner presses Receive/New code.
Recommended, not blocking.

### LOW-2 Revoke while running does not stop the listener
Revoking the last paired device leaves the (auto-started) listener running for the session; next launch does
not auto-start because `paired_devices()` filters `active`. Revoked devices cannot open sessions
(DeviceRegistry). Matches pre-existing manual behaviour; acceptable.

### LOW-3 Test coverage
New test is meaningful (real HTTPS pairing round trip, restart on same store, asserts listener active and
button state; first half also asserts no auto-start when nobody is paired). Not covered: device-store
exception path, revoked-only store (should not auto-start), shutdown-before-timer guard, default-window
non-invocation (MEDIUM-1).

## Checked, no finding
- Only starts when an active (non-revoked) paired device exists; device-store/factory exceptions are caught and
  leave the receiver stopped; `session.start()` errors are caught in `start_receiving`.
- Shutdown race: `_shut_down` set in `shutdown()` before the singleShot can fire; `timer.isActive()` guard
  prevents double start; `closeEvent` calls `capture_inbox.shutdown()` on both close paths.
- Second instance: `claim_single_instance()` exits before a window is built; not affected (but see MEDIUM-1 for
  non-app processes).
- No changes to PackScan/Scan Master/Design Model, metrics or provenance.

## Verdict: CHANGES_REQUIRED
MEDIUM-1 must be fixed (gate auto-start to the real launch path + test). MEDIUM-2 and LOW-1 may be follow-ups
if recorded.
