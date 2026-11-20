# Claude security/licensing review: PR #13 (PL-0451, PL-0452), V01

- Reviewer: independent security/licence reviewer subagent (did not write the code; no source edited)
- Branch `origin/feat/phone-studio-sync`, head `12bcfbafe91cc8099d314151c5a5a3066434f651`, diff against `origin/main` (24 files, +2033/-73)
- CI: run 44831387426 at this head, `gh` reports conclusion success. Jobs passed: capture-e2e, Simulator XCTest, unsigned device archive. Locked Python quality and signing-material scan also passed (`gh pr checks 13`).
- Local run in a detached temp worktree: `uv run pytest tests/transfer tests/studio/test_capture_inbox.py -q` gave 78 passed. `tests/ci/test_artifact_upload_guard_conditions.py` gave 18 passed (it needs `--with pyyaml`).
- Artifact `packlab-capture-e2e-screenshots-44831387426`: 51 PNGs, `manifest.json` and `receiver.log`. Grep found no `device_secret`, `session_token` or private key. `receiver.log` holds only the offer IDs, 127.0.0.1:8443 and expiry times. Screenshot 025 shows a CI loopback pairing code. That offer was one-time and ephemeral and has expired, so this is acceptable. Screenshot 051 shows both scans "Delivered to PackLab".

## Verified OK
- Secret: `secrets.token_urlsafe(32)` (256 bit). Only the SHA-256 is stored, compared with `hmac.compare_digest`. An unknown id and a wrong secret return the same `unpaired` error. `device_revoked` is returned only after the secret matches. Nonces are stored only after the secret matches, and expire after 600 s, so unauthenticated callers cannot fill the store.
- Each token is bound to a `device_id`. `require_session` checks `is_active` on every call, so revocation also ends live tokens. That holds even across the unlocked `_sessions` rebind race. Revocation is persisted by an atomic replace. An unreadable registry fails closed.
- Pairing still needs a one-time offer and code that only Studio creates, so pair spam cannot grow the registry.
- TLS pin (`TransferTLS.swift`) is unchanged. `openDeviceSession` requires `credential.receiver == identity`, so automatic sends go only to the pinned receiver that was paired. Keychain entry uses `AfterFirstUnlockThisDeviceOnly`. HTTP `log_message` is suppressed. Nothing logs secrets.
- The replay harness is compiled out of device builds by `#if targetEnvironment(simulator)` (`UITestReplay.swift:34`) and also needs a launch argument. When it is off, `replay` is nil, so the "Replay: next pose" button cannot appear on a device.
- Backoff is per item, 5 s up to 5 min, and the worker sleeps at most 30 s, so there is no retry storm.
- Thumbnails decode only the app's own accepted photos through ImageIO downsampling.
- No secrets, signing team or identity, new third-party dependencies, assets or private data were added. The replay frames are procedural.

## Findings
- HIGH: none.
- MEDIUM: none.
- LOW-1 `core/src/packlab_core/transfer_security.py:260,278`: expired session tokens are never pruned from `_sessions`, and every successful `/v1/session` rewrites the registry (`pairing.py:283`). A paired device that spams sessions can grow memory and disk I/O without bound. This needs a valid credential.
- LOW-2 `transfer_security.py:278`: `revoke_device` iterates `_sessions` without a lock while ThreadingHTTPServer threads insert into it. It can raise `RuntimeError` to the Qt caller. The revocation itself is already persisted.
- LOW-3 `pairing.py:316`: `chmod 0600` does nothing on Windows, so the code relies on the per-user `%LOCALAPPDATA%` ACL. Exposure is limited because the file holds only hashes.
- LOW-4 `capture_inbox.py:242`: the network-supplied `device_name` goes into a QLabel with AutoText. Set `Qt.PlainText`.
- LOW-5 `PairedSync.swift:181`: phone clock skew over 300 s produces `replayed_request`. The phone treats it as non-terminal, retries every 5 min indefinitely, and shows "not reachable", which is misleading.
- LOW-6 `.github/workflows/packlab-capture-macos.yml:749`: the CI pip install pins versions but not hashes.

## Verdict
CLAUDE_PEER_AUDITED_PASS (security/licence) for PL-0451/PL-0452 Simulator and software scope, with no blocking findings. Behaviour on a physical iPhone 16 (local-network permission, Wi-Fi, background suspension) is EXTERNAL_PENDING_REVIEW. Public and factory release remain blocked until there is real device, legal and signing evidence.
