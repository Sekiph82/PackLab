# PL-0429 Remote iPhone Capture Control (Windows Studio to iPhone on trusted LAN)

## Integrated design: phone long-poll over Transfer V1 (2026-11-21)

This is what Studio and the iOS app implement. The HMAC command prototype further down
(`remote_capture_control.py`) stays as a reference contract; it is not wired to either app.

Trust model is unchanged (paired device credential, fingerprint-pinned TLS, device session
token from `POST /v1/session`). **The phone initiates every connection; Studio never
connects to the phone and the phone opens no listening socket.**

Phone (`RemoteCaptureController`, `PairedSync.swift`):

- Off by default. The operator enables More > "Allow PackLab to trigger captures"
  (persisted in UserDefaults). While on, a purple indicator on the capture screen shows the
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
- Audit log `remote-control-log.jsonl` in the receiver root: `issued`, `delivered`,
  `expired`, `result` (action/outcome/reasons), `rejected_result`. No tokens or secrets.
- Revoke drops the device's pending command and status and wakes its poll, which then
  fails `device_revoked`; the revoked session token is already invalid.
- Capture Inbox > Remote capture shows the selected (or only) paired phone: scan name,
  coverage n/total, instruction and the last result; Capture now / Finish scan are enabled
  only while the phone reports an active scan with control on. Phone text is shown as
  plain text.

Tests: `tests/transfer/test_remote_control.py` (unauthenticated/wrong token, one-shot
delivery, expiry, revoke, unknown result, malformed and oversized status),
`tests/studio/test_capture_inbox.py::test_remote_capture_panel_sends_commands_and_shows_phone_status`,
`tests/ci/test_ios_e2e_remote_relay.py`, Swift `testPL0429*`, and the Simulator E2E
(`capture-e2e`): Studio's Capture now is refused once by the center gate, captures 3
wedges, and Finish scan finalizes the scan, which syncs automatically.

Limits: Simulator replay camera only; no physical iPhone 16, real Wi-Fi or background /
screen-lock behaviour measured. Command latency is not measured. No thumbnail of the last
photo is sent (skipped; add when the owner needs visual confirmation in Studio).

## Reference HMAC command contract (not wired)

Status: **software contract prototype only, feature flag default OFF.** No identified
iPhone 16, trusted LAN or device TLS listener has been tested. Physical acceptance is
still open (see "Physical evidence still required").

Reference implementation: `core/src/packlab_core/remote_capture_control.py`.
Tests: `tests/core/test_remote_capture_control.py`.

## Scope and authority

- Windows Studio (the **controller**) sends capture-control commands to a paired iPhone
  capture app (the **device**). The device responds with capture-control receipts.
- A receipt is **not** capture evidence. Frames still reach Studio only as a finalized
  `.packscan` through PackLab Transfer V1, which is unchanged by this feature.
- Every frame acknowledgement carries `measurement_authority: false`,
  `scan_master_authority: false` and `capture_metadata_status: "placeholder_not_measured"`.
  The controller rejects any acknowledgement that deviates (`authority_upgrade`), even
  when its MAC is valid. Planned turntable angles are plans, not measurements
  (`planned_turntable_angle_mdeg`, integer millidegrees).

## Keys: reuse of the existing pairing

No new pairing, key exchange or cipher. The controller and device share the existing
short-lived Transfer session credential (`PairingStore` + `PairingAuthenticator` in
`pairing.py` / `transfer_security.py`): `token`, `receiver_instance_id`,
`certificate_fingerprint`, `expires_at`.

```
session_id = hex(HMAC-SHA256(key=utf8(token), msg="packlab.remote-capture.session-id.v1"))[0:32]
key[dir]   = HMAC-SHA256(key=utf8(token), msg=canonical_json({
               "controller_id": receiver_instance_id,
               "device_id": <pinned iPhone device id>,
               "direction": dir,          # "controller_to_device" | "device_to_controller"
               "label": "packlab.remote-capture-command.v1",
               "tls_certificate_fingerprint": certificate_fingerprint}))
```

- Separate keys per direction prevent reflecting a command back as a response.
- `device_id` and the TLS pin are bound into the key, so a response from a different
  device, or under a different pin, fails the MAC (device-identity pinning).
- The existing pairing record has no iPhone device identity yet; the device id is pinned
  explicitly when the controller is created. Persisting it in the pairing record is a
  follow-up for the iOS/Studio integration.
- Keys/tokens are never serialised, logged or put in errors; the Python objects that
  hold them refuse `pickle` and redact `repr`.

## Canonical JSON

UTF-8, keys sorted, separators `,` and `:` with no whitespace, `ensure_ascii=false`,
one trailing `\n` (identical to `transfer_protocol.canonical_json`). The receiver
re-serialises the parsed message and rejects it unless the bytes are identical
(`non_canonical`). Additional rules that keep Swift and Python byte-identical:

- **No floating-point numbers anywhere** (`malformed`); all numbers are integers.
- No duplicate keys, no `NaN`/`Infinity`, top level must be an object.
- Identifier strings use restricted ASCII patterns (ids `^[A-Za-z0-9._:-]{1,64}$`, nonce
  and session id 32 lowercase hex, MAC 64 lowercase hex). `/` never appears, so Swift's
  slash escaping is irrelevant, but use `.sortedKeys` and `.withoutEscapingSlashes`.
  Lone UTF-16 surrogates (for example the escape `\ud800`) cannot be re-encoded and are
  rejected as `malformed` on both sides.
- `null` is written as `null`; booleans as `true`/`false`.
- Size bound: 8192 bytes per command and per response (`oversized`).
- Framing on a stream: one message per line (canonical JSON contains no raw newline).

## Command: `packlab.remote-capture-command.v1`

Exactly these keys (unknown keys rejected):

| key | type | notes |
|---|---|---|
| `schema` | string | `packlab.remote-capture-command.v1` |
| `command` | string | allow-list below |
| `session_id` | hex32 | derived from the paired session |
| `controller_id` | id | `receiver_instance_id` of the Studio receiver |
| `device_id` | id | pinned iPhone id |
| `seq` | int 1..2^31-1 | strictly increasing per session |
| `nonce` | hex32 | random, never reused |
| `issued_at_ms` | int | controller Unix time in ms |
| `args` | object | per-command, exact keys |
| `mac` | hex64 | HMAC-SHA256 with `key["controller_to_device"]` over canonical JSON of every other key |

Allow-listed commands and arguments:

| command | args | legal from -> to |
|---|---|---|
| `start_session` | `{"capture_mode": "turntable" \| "guided_orbit" \| "freehand"}` | IDLE -> SESSION_OPEN |
| `set_capture_plan` | `{"steps": [{"ring_id": id, "turntable_angle_mdeg": 0..359999}]}` (1..64 steps) | SESSION_OPEN, PAUSED (unchanged) |
| `capture_frame` | `{}` | SESSION_OPEN/CAPTURING -> CAPTURING |
| `pause` | `{}` | CAPTURING -> PAUSED |
| `resume` | `{}` | PAUSED -> CAPTURING |
| `end_session` | `{}` | SESSION_OPEN/CAPTURING/PAUSED -> CLOSED (terminal) |
| `query_status` | `{}` | any state, unchanged |

`set_capture_plan` replaces the plan and resets the plan cursor. With a plan set,
`capture_frame` beyond the last step is rejected (`capture_plan_complete`). A plan can
only be changed while not capturing (pause first).

## Device verification order

1. feature flag enabled (`feature_disabled`)
2. peer address is loopback/RFC1918/ULA/link-local literal (`non_lan_peer`)
3. size, strict JSON, canonical bytes, exact key set and types, command allow-list and args
4. a paired session exists, `session_id` matches
5. `controller_id`/`device_id` match. Failures in 4-5 all return the single wire code
   `unauthenticated` so an unauthenticated peer cannot learn whether the device is paired
   or which ids are valid. The specific reason (`unpaired_session`, `unknown_session`,
   `identity_mismatch`) is kept only in the device's local rejection log.
6. MAC, constant-time (`bad_mac`)
7. session not expired (`session_expired`)
8. `|device_now_ms - issued_at_ms| <= 30000` (`stale_command`)
9. `seq > last_accepted_seq` and nonce not among the last 256 (`replayed_command`);
   the seq and nonce are then consumed, even if later steps reject
10. rate limit: at most 10 authenticated commands per rolling second (`rate_limited`),
    measured with a monotonic clock so wall-clock steps cannot lock the device out or
    reset the window; the limit must be an integer in 1..1000
11. state machine (`illegal_transition`, `capture_plan_complete`)

Failures in steps 1-9 return an **unsigned** rejection
`{"error_code": <code>, "schema": "packlab.remote-capture-response.v1", "status": "rejected"}`
that the controller treats as untrusted (`device_rejected_unauthenticated`). Failures
in steps 10-11 and successes return a signed response; only `rate_limited`,
`illegal_transition` and `capture_plan_complete` may appear as signed rejections. Any
unexpected internal exception is converted to an unsigned `malformed` rejection rather
than crashing the endpoint. The local rejection log keeps codes only (no payloads) and
is bounded to the last 256 entries.

## Response: `packlab.remote-capture-response.v1`

Keys: `schema`, `session_id`, `controller_id`, `device_id`, `in_reply_to_seq`,
`in_reply_to_nonce`, `command`, `status` (`ok`/`rejected`), `state`, `error_code`
(`null` when ok), `result`, `issued_at_ms`, `mac` (HMAC-SHA256 with
`key["device_to_controller"]`).

`result` always contains device status: `state`, `capture_mode`, `frames_captured`,
`plan_steps_total`, `plan_steps_remaining`, `last_accepted_seq`. An ok `capture_frame`
also contains `frame` with exactly: `frame_index`, `plan_step`, `ring_id`,
`planned_turntable_angle_mdeg`, `device_capture_timestamp_ms`,
`capture_metadata_status`, `measurement_authority`, `scan_master_authority`.

`result` keys are exact: the status keys only, plus `frame` only for an `ok`
`capture_frame`. A `frame` on any other response (for example `query_status`, or a
rejected capture), and any extra key (for example `scale_mm_per_px` or an
`*_authority` key), are rejected as `malformed`. A frame claiming authority or a
non-placeholder metadata status is rejected as `authority_upgrade`.

## Controller verification order

1. the pairing session is still valid via `PairingAuthenticator.require_session`
   (`unpaired_session`/`session_expired`); this is checked on every `build` **and** every
   `accept_response`. Note that `PairingAuthenticator` purges an expired credential the
   first time it sees it, so later calls report `unpaired_session`.
2. size, strict JSON (integers only, no duplicate keys, no lone surrogates), canonical bytes
3. unsigned rejection envelope -> `device_rejected_unauthenticated` (device code is
   reported only if it is a known code, otherwise `malformed`)
4. exact key set; MAC must be 64 lowercase hex and match, constant-time (`bad_mac`)
5. `session_id` (`unknown_session`), `controller_id`/`device_id` (`identity_mismatch`)
6. pending `(seq, nonce, command)` match, accepted once (`unexpected_response`);
   responses may arrive out of order. At most 64 commands stay pending; older ones are
   evicted and their late responses become `unexpected_response`.
7. exact response contract: `state`/`status`/`error_code` enums, `issued_at_ms` integer,
   status fields integer-typed and bounded, `capture_mode` in the allow-list or `null`,
   `result.state` equal to the top-level `state`, `plan_steps_remaining <= plan_steps_total`,
   and frame fields typed (`frame_index`/timestamps integers, plan fields all present or
   all `null`, `ring_id` matching the id pattern). Failures -> `malformed`.
8. any other unexpected exception while parsing is converted to `malformed`.

When the sequence space is exhausted (`seq` would exceed 2^31-1) the controller refuses to
sign more commands (`session_expired`); pair again.

### What each side validates

| check | controller | device |
|---|---|---|
| feature flag | at construction | every message |
| LAN peer literal | at construction (device address) | every message (sender address) |
| canonical/strict JSON, size | responses | commands |
| identifier patterns and integer types | its own commands at build; response fields after MAC | every command field before MAC |
| MAC | responses | commands |
| session validity | `require_session` on build and receipt | credential `expires_at` |
| timestamp window, seq/nonce replay | no (responses are bound to pending seq+nonce) | yes |
| rate limit | no | yes |
| authority isolation | yes | produces placeholders only |
| TLS | **not enforced in code** | **not enforced in code** |

## Fault semantics

- Dropped command: no effect; the next command with a higher seq is accepted.
- Duplicated or reordered (older seq) command: `replayed_command`, never re-executed.
- Delayed beyond 30 s: `stale_command`.
- Lost acknowledgement: the controller must **not** blindly resend `capture_frame`; it
  reconciles with `query_status` (`frames_captured`, `last_accepted_seq`). Resending the
  same bytes is rejected as a replay, so a frame can never be captured twice by
  retransmission.
- Tampered command or response: `bad_mac` (or a schema/canonical error).

## Policies and flags

- Feature flag default off on both sides (`enabled=False`). Nothing in Studio or the iOS
  app is wired to this module yet.
- LAN policy accepts only `127/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, `::1`,
  `fc00::/7`, `fe80::/10` (IPv4-mapped IPv6 unwrapped). Hostnames, CGNAT `100.64/10`,
  documentation, multicast, broadcast and public addresses are rejected. **This does not
  validate that the LAN is trusted**; a hostile device on the same private network is
  stopped only by TLS pinning and the MAC layer.
- Known admissions of this coarse literal policy: the whole IPv4 link-local range is
  admitted, including the cloud metadata literal `169.254.169.254`, and IPv6 literals with
  a zone id (for example `fe80::1%eth0`) are accepted with the zone ignored. Both are
  intentional for ad-hoc/peer-to-peer Wi-Fi and are covered by tests.
- Production transport must be TLS 1.2+ with the existing certificate pin. **This module
  does not enforce TLS**: it is transport-agnostic and never sees the socket, so no
  `insecure_transport` code is produced here; the TLS requirement must be enforced by the
  Studio transport and the iOS client. The loopback socket test in the suite is plaintext
  on `127.0.0.1` and proves framing only.
  Recommended iOS shape: the iPhone opens the outbound pinned TLS connection to the
  Studio receiver it already trusts and receives commands over it, so the iPhone needs
  no listening socket or server certificate.

## iOS implementation checklist (not done in this pass)

- Swift canonical encoder and HMAC (CryptoKit `HMAC<SHA256>`), byte-compared against
  Python-generated golden vectors.
- Device state machine mapped to the existing capture engine (`CaptureModeID`,
  session foundation); `capture_frame` triggers the normal capture path so that frames
  only leave the phone inside a finalized `.packscan`.
- Persist `last_accepted_seq`/nonce memory per session; on app relaunch treat the
  session as closed rather than resetting replay state.
- Operator-visible indicator and local cancel whenever remote control is active.

## Physical evidence still required (keeps PL-0429 physical acceptance open)

- Identified iPhone 16 running a build that implements this contract.
- Trusted LAN (network identity, Wi-Fi isolation settings, who else is on it).
- Measured command-to-capture latency and jitter, packet-loss behaviour, clock skew
  between Windows and iPhone versus the 30 s window.
- TLS on device with the existing certificate pin, including pin mismatch rejection.
- Background/foreground, screen-lock and interruption behaviour of a remote session.
- Swift/Python golden-vector interoperability of canonical bytes and MACs.
