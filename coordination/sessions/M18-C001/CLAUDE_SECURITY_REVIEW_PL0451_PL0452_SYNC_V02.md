# Claude security review: PR #18 sync hardening (follow-up to V01), V02

- Reviewer: independent security reviewer subagent (did not write the code; no source edited)
- Branch `origin/fix/sync-hardening`, head `07544dc6d9efefa03fc4db2e84a5361aeeea046f`, single commit, 9 files (+207/-27)
- CI verified at 07544dc6 with `gh`:
  - Windows Python Quality 44835497947: success
  - Capture macOS 44835497985: success (Simulator XCTest, device archive, Simulator E2E)
  - Signing Material Guard 44835498765: success
- Local run in a detached temp worktree (removed afterwards): `uv run pytest tests/transfer tests/studio/test_capture_inbox.py -q` gave 81 passed. Three new tests cover pruning/coarse last_seen, revoke under concurrent sessions, and name sanitization.

## V01 findings
- LOW-1 RESOLVED:
  - `_add_session` (`transfer_security.py`) prunes expired tokens under the lock on every insert.
  - `last_seen_at` is persisted at most once per 60 s per device (`pairing.py`, `LAST_SEEN_PERSIST_SECONDS`). Tradeoff: last-seen is only accurate to 60 s, and the in-memory value is not refreshed in between. Acceptable for a display field.
  - Residual: live tokens within one 300 s TTL are still unbounded for an authenticated device. Accepted.
- LOW-2 RESOLVED: every `_sessions` read and write goes through `_sessions_lock`.
  - The lock is non-reentrant, but it is never nested.
  - `revoke_device` takes the registry lock and then the sessions lock one after the other, never both at once, so there is no lock-order inversion or deadlock.
  - `is_active` is called outside the sessions lock.
- LOW-4 RESOLVED: `_clean_device_name` drops Unicode category C (Cc/Cf/Cs/Co/Cn).
  - Probe results: U+202E, ZWSP/ZWJ, NUL and lone surrogates are removed. Whitespace is collapsed and the name is capped at 64 characters. An empty result falls back to "iPhone".
  - HTML stays as literal text, which is safe because `status_label` is now `PlainText` and QListWidgetItem is plain text.
  - Residual: names already stored by PR #13 are not re-sanitized when loaded. Negligible.
- LOW-5 RESOLVED: `replayed_request` from `/v1/session` now becomes `clockSkew`.
  - The skew value comes from the receiver's HTTP `Date` header, which arrives inside the pinned TLS channel. It only selects an integer shown in a status message, and retries continue with the 5-minute cap.
  - A receiver could only influence that message, and it would need to pass the TLS pin first.
  - With a missing Date header the phone shows "phone clock is off", which is the expected fallback.
  - A 240 s threshold against the 300 s window is sound.
- LOW-3 and LOW-6 remain open and informational; neither blocks this PR.

## Verdict
CLAUDE_PEER_AUDITED_PASS for PR #18. No new HIGH, MEDIUM or LOW findings. Behaviour on a physical iPhone 16 remains EXTERNAL_PENDING_REVIEW, and public/factory release remains blocked.
