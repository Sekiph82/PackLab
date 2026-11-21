# Claude security review: PR #20 PL-0429 remote capture control, V01

- Reviewer: independent security reviewer subagent (did not write the code; no source edited)
- Branch `origin/feat/remote-capture-control`, head `dcbdfc993c40cbd0de990f8d8054997b21a5775d` (3 commits, includes PR #18 07544dc6), 17 files (+1350/-39)
- CI verified at dcbdfc99 with `gh`:
  - Windows 44847842541: success
  - macOS 44847842585: success (Simulator XCTest including `testPL0429RemoteCommandGatesOnThePhone`, device archive, and the E2E job; its screenshots show remote-connected, refused-by-gate and remote-capture-1/2)
  - Signing guard 44847842525: success
- Local run in a detached temp worktree (removed afterwards): `uv run --with pyyaml pytest tests/transfer tests/studio/test_capture_inbox.py tests/ci/test_ios_e2e_remote_relay.py tests/core/test_remote_capture_control.py -q` gave 209 passed.

## Verified OK
- **Authorization binding:**
  - `require_session` now returns the token's `device_id`, and both control routes refuse an empty id (`receiver.py` do_GET/do_POST).
  - `next_command` pops only `_pending[device_id]`.
  - `report` accepts a result only if `_delivered[command_id].device_id` matches the caller, otherwise `unknown_command`, and the action must match.
  - A phone cannot issue commands: `issue` is reachable only from the Studio UI.
  - Revoke checks `is_active` inside the poll loop, and `forget` wakes open polls.
- **Malicious paired phone:** it can only post bounded status text and consume its own commands. It has no access to other devices, no file paths, and no measurement or Scan Master fields.
- **Status injection:**
  - `parse_status` is strict: exact key sets, bool and int types, ints 0..1000, reason regex, at most 8 reasons, text at most 128/256 characters with category C stripped, body at most 4096 bytes.
  - `remote_label` is `PlainText`, and `status_label` is `PlainText` since PR #18.
- **Replay:**
  - Each command is consumed on delivery, expires after 10 s, and is never redelivered by the receiver.
  - Pinned TLS blocks network replay.
  - The phone's 64-entry in-memory memory is a second line of defence. Losing it on restart is harmless because the receiver never resends.
- **Capture gates:** `capture` goes through `admitCapture` and `requestManualCapture`, so every production gate applies. The E2E run demonstrated a gate refusal.
- **Finish:** `finish` uses the normal Finalize, which exports a package. Nothing is deleted, and the package is enqueued only to the pinned paired receiver. There is no data loss.
- **Privacy:** no image or camera stream and no measurements are sent. Polling happens only when control is on, a scan is active and the phone is paired.
- **Unauthenticated drain:** a bad `Content-Length` raises ValueError, which becomes a 400. The drain is capped at 1 MB under the 30 s socket timeout.
- **Prototype:** `core/src/packlab_core/remote_capture_control.py` already exists on main. In this branch it is imported only by `tests/core/test_remote_capture_control.py`, and the docs mark it unwired.

## Findings
- HIGH: none.
- MEDIUM: none.
- LOW-1 `receiver.py` (`_ExclusiveHTTPServer`, ThreadingHTTPServer): there is no per-device cap on concurrent long-polls. One paired phone can hold many threads for 25 s each. This needs a valid device session and is revocable. The pre-existing unauthenticated connection threads (30 s timeout) are already unbounded. Suggest a cap of one or two polls per device.
- LOW-2 `remote_control.py` `_record`: `remote-control-log.jsonl` grows without limit. A paired phone can spam `rejected_result` entries. The file is also written while holding the hub Condition. Suggest rotation or a size cap, or rate-limiting `rejected_result`.
- LOW-3 `PairedSync.swift` `RemoteCaptureController.enabled`: the opt-in is persisted in UserDefaults, so after the first opt-in it stays on across launches. It is mitigated by the always-visible purple indicator, which also turns control off. Consider resetting the opt-in at the start of each scan.
- LOW-4 `capture_inbox.py` Finish scan: the button sends without confirmation. A misclick finalizes the phone's scan early. Nothing is lost, but the scan is closed. Suggest a confirm dialog.
- LOW-5: `remote_capture_control.py` is a dead prototype in a public repo. Consider deleting it or moving it to `docs/` once PL-0429 is accepted.

## Verdict
CLAUDE_PEER_AUDITED_PASS (security) for PR #20 in software/Simulator scope. No blocking findings. Latency, Wi-Fi and background behaviour on a physical iPhone 16 remain EXTERNAL_PENDING_REVIEW. PL-0429 physical validation and public/factory release remain blocked.
