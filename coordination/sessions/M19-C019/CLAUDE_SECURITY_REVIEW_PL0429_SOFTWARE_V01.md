# PL-0429 software half: independent security review V01

Reviewer: Claude Code security/license reviewer subagent. I did not implement this code and made no source edits.
Scope: the untracked files core/src/packlab_core/remote_capture_control.py, tests/core/test_remote_capture_control.py and docs/development/PL-0429_REMOTE_CAPTURE_PROTOCOL.md, plus the reused transfer_protocol.canonical_json and transfer_security SessionCredential/PairingAuthenticator.
Physical status: no identified iPhone 16, trusted LAN or device TLS listener. PHYSICAL VALIDATION PENDING.

## Commands run (local, Windows, .venv)
- pytest -q tests/core/test_remote_capture_control.py tests/transfer: 125 passed, 1 pre-existing zipfile warning
- ruff check on both files: all checks passed
- ruff format --check with line-ending set to auto (the CI form in .github/workflows/windows-python-quality.yml:129): 2 files already formatted. Without auto, the format check flags only the CRLF line endings of the module.
- mypy on both files: no issues found
- Adversarial probes and a 30-mutant test run, all against a scratch copy outside the repo. The only socket in the suite binds to 127.0.0.1:0.
- Secret/PII grep of the three files found nothing. The fixtures are synthetic (pin of 64 "a" characters, studio-1, iphone-16-a, RFC1918 addresses).

## Verified correct
- The device checks the MAC before it consumes seq or nonce, so a forged command cannot burn sequence numbers. A mutant that consumed seq before the MAC was killed.
- Strict parse: duplicate keys are rejected, NaN/Infinity are rejected, floats are rejected, the input must be byte-exact canonical, there is an 8192-byte bound, and deep nesting returns malformed. The type(x) is int check excludes bool.
- Key derivation: there is one key per direction, and each key is bound to controller_id, device_id and the TLS pin. A response can only be accepted once and only for a pending seq. Reflecting a command back fails the MAC. The session_id label cannot collide with the canonical-JSON key-derivation messages.
- LAN policy: IPv4-mapped IPv6 is unwrapped and public addresses are rejected. Hostnames, whitespace and an IPv4 address with a percent suffix are rejected. 6to4, NAT64 and IPv4-compatible addresses are rejected.
- Key holders refuse pickling and redact their repr. Error messages are fixed strings and are raised from None.
- The feature flag is off by default on both sides.

## Findings

### P2-1 Unauthenticated input raises uncaught exceptions on both the device and the controller (crash / DoS)
All of these were reproduced in the scratch copy:
- remote_capture_control.py:220: canonical_json(value) runs outside the try block. A JSON lone surrogate (the escaped string \ud800 in any string value) raises UnicodeEncodeError. On the device this escapes handle() (:517 catches only RemoteCaptureError). The controller accept_response has the same problem.
- remote_capture_control.py:239: the CAPTURE_MODES membership test raises TypeError (unhashable) when capture_mode is a JSON list. This happens before the MAC check, so any LAN peer can trigger it.
- remote_capture_control.py:295: on the controller, the response mac is not validated against the regex. A non-ASCII str MAC makes hmac.compare_digest raise TypeError.
- remote_capture_control.py:446: an unhashable status in a signed response raises TypeError. This needs an authenticated device, so its severity is lower.

Fix:
- Wrap the canonical_json call at :220 so that UnicodeEncodeError and ValueError become MALFORMED.
- Add isinstance(str) checks before each set/frozenset membership test (:239 and :446).
- Validate the response mac with _HEX64_RE before verify.
- Add a defensive catch-all in handle() that returns an unsigned malformed rejection.
- Add regression tests for each case.

### P2-2 A signed device response can carry unvalidated or authority-like content (the claim that acks can never claim authority is only partly true)
- remote_capture_control.py:448 checks only that _STATUS_KEYS is a subset of the result keys. Extra keys are allowed, and value types are never checked.
- :450: the authority and frame checks run only when the command is capture_frame and the status is ok.

In the scratch copy, the controller accepted and returned all of the following:
- a query_status result containing a frame with measurement_authority true and scan_master_authority true, plus top-level measurement_authority true and scale_mm_per_px
- a rejected capture_frame that carried an authority-claiming frame
- an ok frame with frame_index "zero" and ring_id as an object, plus an extra scan_master key
- frames_captured "lots", issued_at_ms "x", and result.state disagreeing with the top-level state

The device is authenticated, but the doc (lines 124-128) promises an exact contract, and the response layer is where Studio would consume the data.

Fix:
- Require exact result keys: _STATUS_KEYS, plus frame only for an ok capture_frame.
- Type-check the status fields: ints, capture_mode limited to CAPTURE_MODES or None, and result.state equal to state.
- Type-check the frame fields: int or None, and ring_id matching _ID_RE or None.
- Type-check issued_at_ms.
- Reject frame outside an ok capture_frame.

### P3-1 Test-discrimination gaps
These mutants survived the suite:
- dropping parse_float rejection
- dropping the pending nonce match (:427)
- dropping the pending command match (:427)
- removing the TLS fingerprint from key derivation (:283), even though the doc claims pin binding
- dropping the controller session_id/identity checks (:417-423; these are redundant behind the MAC, but no test discriminates them)
- the result-subset check (:448)
- the exact frame keys check (:452)
- MAX_PENDING eviction (:392)
- the MAX_SEQ guard (:371)

Fix: add one targeted negative test for each. Use a forged response signed with the real device key, a credential that differs only in fingerprint, a float in a command, and pending overflow plus seq exhaustion with a seeded counter.

### P3-2 The device returns specific unauthenticated rejection codes before the MAC check (oracle)
At :565-573, unpaired_session, unknown_session and identity_mismatch are returned to any LAN peer before the MAC check. This leaks whether the device is paired and which controller_id/device_id are valid. The session_id is 128-bit, so it is not guessable.
Fix: before the MAC, collapse these three to a single generic code. Keep the detail in local logs only.

### P3-3 Mock robustness and stale fields
- self.rejections (:503, :519) grows without bound on unauthenticated traffic. Cap it with a bounded deque or a counter.
- _rate_limit (:593) uses the wall clock. If the clock steps backwards, the device stays rate-limited. Use time.monotonic for the rate limiter.
- max_commands_per_second is not validated, so it can be 0 or negative.
- accept_response does not re-check session expiry. It is only enforced in build.

### P3-4 Doc/code honesty notes
- INSECURE_TRANSPORT (:356) is never produced, because require_session is called without transport. TLS is a documented requirement only, not enforced in code. The doc does say this, but the mapping suggests otherwise. Either remove the mapping or add a comment.
- The LAN allow-list admits 169.254.169.254 (cloud metadata) and accepts IPv6 zone IDs. This is acceptable as a coarse literal policy. Mention it in the doc.
- The doc says all strings are ASCII from restricted patterns. That is enforced only on the device side. The controller does not enforce it before the MAC (see P2-1).

## Secrets / licensing
No tokens, keys, .env values, signing material, private scans, supplier data or PII are in the three files. There are no new dependencies (stdlib only), so there is no license impact.

## Verdict
FAIL (software half). The two P2 issues are small, local fixes. P2-1 lets an unauthenticated LAN peer raise uncaught exceptions out of handle()/accept_response(). P2-2 contradicts the documented exact response contract and the authority-isolation claim.

Once both P2s are fixed and covered by regression tests, and the P3-1 test gaps are closed, I expect re-review to reach SOFTWARE_PASS_WITH_NOTES. Physical acceptance remains PHYSICAL VALIDATION PENDING in any case.
