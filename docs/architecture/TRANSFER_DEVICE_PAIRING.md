# Transfer V1: pair once, then automatic sync (PL-0452)

PackLab Transfer V1 (`packlab-transfer`, protocol version `1`, HTTPS only) moves a finalized
`.packscan` from PackLab Capture (iPhone) to the PackLab Studio receiver.

## Pairing (once)

1. Studio shows a one-time offer (QR or manual fields): receiver instance ID, host, port,
   pairing ID, 8-character code, expiry (max 15 min), and the SHA-256 pin of the receiver's
   self-signed TLS leaf certificate.
2. The phone pins that fingerprint for every connection and calls `POST /v1/pair` with the
   offer, the code, the fingerprint and an optional `device_name` (hardware model).
3. Studio consumes the offer (replay -> `replayed_pairing`, expired -> `expired_pairing`) and
   returns a 300 s `session_token` **plus a long-lived device credential**
   (`device_id`, `device_secret`). The secret is returned only here.
4. The phone stores receiver identity + device credential in the Keychain
   (`kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`). Studio stores only
   `sha256(device_secret)` in `paired-devices.json` under its private receiver root
   (`%LOCALAPPDATA%`-side data, never in Git).

## Later connections (no code)

`POST /v1/session` with `message: device_session`, `receiver_instance_id`, `device_id`,
`device_secret`, a fresh `nonce` (16-128 chars) and `timestamp` (Unix seconds) returns a
fresh 300 s `session_token` bound to that device. Rules:

| Condition | Error code |
|---|---|
| unknown device or wrong secret (indistinguishable) | `unpaired` |
| device revoked in Studio | `device_revoked` (only after the secret matched) |
| timestamp more than 300 s from the receiver clock, malformed nonce, or nonce reuse | `replayed_request` |
| other receiver instance ID | `wrong_receiver` |

The secret only travels inside the pinned TLS channel; nonce/timestamp checks are defence
in depth against a replayed request. Revoking a device (Studio Capture Inbox > Paired
devices > Revoke) also ends its live session tokens. Transfers then use the existing
`/v1/transfers` create / chunk / status / complete routes with `Authorization: Bearer`.

## Phone queue

At Finalize, a paired phone queues the package (Application Support/PackLabSync/queue.json)
and sends it when the receiver answers; failures retry with backoff (5 s doubling to 5 min).
A stable transfer ID per package lets the receiver resume from its checkpoint, and an item
interrupted by an app exit resumes as queued. History shows `Queued for PackLab`,
`Sending x%`, `Delivered to PackLab` or `Failed: reason`. `device_revoked` / `unpaired`
forget the stored pairing and stop retrying; Send to PackLab then pairs again.

## Remote capture control (PL-0429)

Same trust model, phone-initiated: while a scan is active and the operator chose
More > Allow PackLab to trigger captures (default off, an on-screen purple indicator stops
it), the phone long-polls `GET /v1/control/next` and pushes `POST /v1/control/status` with
its device session token. Studio's Capture Inbox > Remote capture shows the pushed status
and offers Capture now / Finish scan; each is a one-shot command (10 s expiry, one pending
per device, logged to `remote-control-log.jsonl`). The phone runs it as a Manual Capture
tap or Finalize with every production gate and reports the outcome. Revoke ends control.
Contract: `docs/development/PL-0429_REMOTE_CAPTURE_PROTOCOL.md`.

## Limits

The stored host/port are used as-is: a changed PC IP address or receiver port needs a new
pairing (no service discovery yet). Physical iPhone behaviour (local-network permission,
Wi-Fi, background suspension) is not proven by the Simulator harness (PL-0451).
