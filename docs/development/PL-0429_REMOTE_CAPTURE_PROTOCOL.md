# PL-0429 Remote iPhone Capture Control (Windows Studio to iPhone on trusted LAN)

## Integrated design: phone long-poll over Transfer V1 (2026-11-21)

This is what Studio and the iOS app implement. The earlier unwired HMAC command prototype
(`remote_capture_control.py`) was deleted after the security review (LOW-5); see git history.

Trust model is unchanged (paired device credential, fingerprint-pinned TLS, device session
token from `POST /v1/session`). **The phone initiates every connection; Studio never
connects to the phone and the phone opens no listening socket.**

Phone (`RemoteCaptureController`, `PairedSync.swift`):

- Off by default. The operator enables More > "Allow PackLab to trigger captures"
  (never persisted: it is off again after every app launch). While on, a purple indicator on the capture screen shows the
  connection state; tapping it turns control off.
- Polls only while control is on, a scan is active and a pairing exists:
  `GET /v1/control/next` (`Authorization: Bearer <device session token>`). The receiver
  holds it up to 25 s; 204 = no command, 200 = `{"message":"remote_command",
  "command_id":<32 hex>,"action":"capture"|"finish","expires_in_ms":int}`.
- Pushes `POST /v1/control/status` (strict keys, at most 4096 bytes): `scan_active`,
  `control_enabled`, `scan_name` (<=128 scalars), `coverage_captured`/`coverage_total`
  (required-ring wedges, ints 0..1000), `instruction` (<=256, the on-screen guidance text),
  optional `last_result` = {`command_id`, `action`, `outcome`
  (`captured`/`refused`/`finished`/`failed`), `reasons` (<=8 codes `^[a-z0-9_]{1,64}$`),
  `message` (<=256)}. Sent on connect, after each command and whenever it changes (1 s
  check). No image, no camera stream, no measurement or scale fields.
- Phone-side refusals before anything runs: `remote_control_disabled`, `command_expired`,
  `no_active_scan`, `replayed_command` (last 64 executed ids). An unknown action fails to
  decode and is ignored.
- `capture` = exactly a Manual Capture tap: device admission (`health_hard_stop`) and then
  `requestManualCapture`, i.e. every production gate (object center set, live frame fresh,
  object in view, camera above the table, quality coordinator, persistence). Refusal
  reasons and the operator hint are reported back. `finish` = History Finalize of the
  active session, then automatic delivery to the paired PackLab.
- `device_revoked` disables control; any other error drops the session and reconnects with
  a fresh device session after 3 s.

Studio (`packlab_studio/remote_control.py`, routes in `receiver.py`, panel in
`capture_inbox.py`):

- `RemoteControlHub.issue(device, action)` refuses unless the device is paired and active
  (`device_revoked`), polled within 40 s (`device_not_connected`) and has no unexpired
  pending command (`command_pending`; a double click is not two captures).
- Commands are one-shot (removed when delivered), expire 10 s after issue (`expired` in the
  log, never delivered late), bound to the device id of the session token that polls.
- A `last_result` must name a command delivered to that same device (`unknown_command`
  otherwise); a repeated status does not log the result twice.
- Long-polls: a newer poll from the same device ends its older poll at once with 204; at
  most 16 polls wait across all devices (`too_many_polls`).
- Audit log `remote-control-log.jsonl` in the receiver root: `issued`, `delivered`,
  `expired`, `result` (action/outcome/reasons), `rejected_result`. No tokens or secrets.
  Written outside the hub lock; rotates to `remote-control-log.jsonl.1` at 1 MiB (one
  rotated file kept).
- Revoke drops the device's pending command and status and wakes its poll, which then
  fails `device_revoked`; the revoked session token is already invalid.
- Capture Inbox > Remote capture shows the selected (or only) paired phone: scan name,
  coverage n/total, instruction and the last result; Capture now / Finish scan are enabled
  only while the phone reports an active scan with control on; Finish scan asks for
  confirmation first. Phone text is shown as plain text.

Tests: `tests/transfer/test_remote_control.py` (unauthenticated/wrong token, one-shot
delivery, expiry, revoke, unknown result, malformed and oversized status),
`tests/studio/test_capture_inbox.py::test_remote_capture_panel_sends_commands_and_shows_phone_status`,
`tests/ci/test_ios_e2e_remote_relay.py`, Swift `testPL0429*`, and the Simulator E2E
(`capture-e2e`): Studio's Capture now is refused once by the center gate, captures 3
wedges, and Finish scan finalizes the scan, which syncs automatically.

Limits: Simulator replay camera only; no physical iPhone 16, real Wi-Fi or background /
screen-lock behaviour measured. Command latency is not measured. No thumbnail of the last
photo is sent (skipped; add when the owner needs visual confirmation in Studio).

