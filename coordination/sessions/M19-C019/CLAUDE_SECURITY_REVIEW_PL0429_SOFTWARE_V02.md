# PL-0429 software half: independent security re-review V02

Reviewer: Claude Code security/license reviewer subagent. I did not implement this code.
I made no source edits and no git writes.
HEAD is 934d2d35. The three reviewed files are still untracked:
- core/src/packlab_core/remote_capture_control.py (743 lines)
- tests/core/test_remote_capture_control.py (809 lines)
- docs/development/PL-0429_REMOTE_CAPTURE_PROTOCOL.md (238 lines)

Prior review: CLAUDE_SECURITY_REVIEW_PL0429_SOFTWARE_V01.md (FAIL: two P2 findings, four P3 findings).
Physical status: no identified iPhone 16, trusted LAN or device TLS listener, so physical validation is still pending.

## Commands run (local .venv)
- pytest -q tests/core/test_remote_capture_control.py: 111 passed
- pytest -q tests/core/test_remote_capture_control.py tests/transfer: 173 passed, 1 pre-existing zipfile warning
- ruff check: clean
- ruff format --check, with line-ending set to auto as CI runs it: clean
- mypy on both files: no issues
- Adversarial probes (26 cases) and 51 mutants. Both ran on a scratch copy outside the repo, with pytest pythonpath pointed at that copy. The only socket in the suite binds to 127.0.0.1:0.
- Secret/PII grep of the three files: nothing found. The module imports the standard library only and adds no new dependency or license.

## V01 findings re-checked against the source

### P2-1 Unauthenticated crash paths: FIXED
Code changes:
- :226-229 wraps the canonical re-encode, so a lone surrogate now becomes malformed.
- :243 adds _is_capture_mode, so a list-valued capture_mode now becomes bad_args.
- :313 makes verify regex-check the MAC before compare_digest, so a non-ASCII MAC now becomes bad_mac.
- :348 adds _enum, which handles non-str values.
- :464-469 and :606-611 add catch-alls in accept_response and handle.

Probe results:
- Every V01 crash input now returns a RemoteCaptureError or an unsigned malformed / bad_args / bad_mac rejection.
- Non-bytes input, peer=None and an unhashable signed status are also handled.

### P2-2 Signed response content: FIXED
Code changes:
- _validate_signed (:505-542) enforces exact result keys, with frame allowed only for an ok capture_frame.
- It checks state and enum types, and that result.state equals the top-level state.
- It enforces integer-typed, bounded status fields, and plan_steps_remaining <= plan_steps_total.
- It types issued_at_ms.
- A signed rejection may only carry rate_limited, illegal_transition or capture_plan_complete.
- An ok response must carry error_code null.
- _validate_frame (:357-375) types every frame field and requires the plan fields to be all present or all null.

Probe results:
- These forged signed responses, made with the real device key, were all rejected:
  - a query_status carrying an authority frame
  - an extra scale key
  - a rejected capture_frame carrying a frame
  - a signed bad_mac code
  - a mismatched state
  - frames_captured as a string
  - partially filled plan fields
  - an ok response with an error_code
  - a bool issued_at_ms
- measurement_authority=0 is rejected as authority_upgrade.
- A valid frame is still accepted.

### P3-1 Test discrimination: FIXED
All nine V01 survivors are now killed:
- float rejection
- pending nonce match and pending command match
- TLS pin in key derivation
- controller session_id and identity checks
- exact result keys and exact frame keys
- MAX_PENDING
- MAX_SEQ

### P3-2 Pre-MAC oracle: FIXED
- :660-674 returns the single wire code unauthenticated for unpaired, unknown-session and identity mismatch. The detail is kept only in the local deque.
- Probe: a wrong session, a wrong device and a revoked pairing all return unauthenticated.

### P3-3 Mock robustness: FIXED
- The rejection log is a deque bounded to 256 (:594).
- The rate limiter uses an injectable monotonic clock (:573, :694).
- The rate parameter is validated to 1..1000 (:577).
- accept_response re-checks the session (:463).

### P3-4 Doc honesty: FIXED
- The INSECURE_TRANSPORT mapping is removed, and a comment states that TLS is not enforced in this module (:413-414).
- The doc now covers 169.254.169.254 and zone ids, the controller verification order, and the expiry-then-unpaired behaviour.

## Mutation run (51 mutants, scratch copy)
- 49 mutants were killed. That includes all V01 mutants plus new ones for every V02 change: oracle leak, rejections_unbounded, rate_wall_clock, mac_no_regex, signed_any_reject_code, state consistency, status types, steps order, timestamp type, all-or-none plan fields, rate parameter, controller catch-all, capture_mode hashing, and the session re-check on accept.
- 2 mutants survived. Both remove redundant defensive layers:
  - narrowing the surrogate except at :228 (the catch-alls still convert the error)
  - narrowing the device catch-all at :609 (no remaining input reaches it, because every known crash path is fixed upstream)

  I accept both as defense in depth (note N2).

## Remaining notes (non-blocking)
- N1 (P3): a residual, narrow oracle. A peer that already knows the 128-bit session_id plus both ids gets bad_mac rather than unauthenticated. Getting there needs the HMAC-derived session id, which is not guessable. Optional fix: map bad_mac to unauthenticated on the wire as well.
- N2 (P3): the two surviving mutants above are redundant safety nets. Optionally, add a test that monkeypatches _apply to raise, to pin the device catch-all.
- N3: TLS and the trusted-LAN assumption remain contractual only. Real transport pinning, Swift/Python golden vectors, latency, clock skew, and iOS lifecycle behaviour need physical evidence (doc section "Physical evidence still required").

## Verdict
SOFTWARE_PASS_WITH_NOTES.
The software half is complete, and physical validation is still pending. Do not mark PL-0429 physical acceptance or any public/factory release on the basis of this review.
