# Claude security review: PR #21 PL-0429 remote-control LOW follow-ups, V02

- Reviewer: independent security reviewer subagent (did not write the code; no source edited)
- Branch `origin/fix/remote-control-lows`, head `a461ef9514d4c5968cf725b7566eede88033bc7c` (2 commits), 11 files (+183/-1842)
- CI verified at a461ef95 with `gh`:
  - Windows 44851645420: success
  - macOS 44851645403: success (Simulator XCTest, device archive, E2E)
  - Signing guard 44851645442: success
- Local run in a detached temp worktree:
  - tests/transfer + tests/studio/test_capture_inbox.py + tests/ci: 523 passed, 4 failed.
  - All 4 failures are in `tests/ci/test_packlab_test_runner_behavior.py` (disk-budget child-tree tests). They fail identically on origin/main locally, so they are owner-host environment failures, not regressions. Windows CI passes them.
- Independent concurrency probe against `RemoteControlHub` at a461ef95 (scratchpad script). A newer poll from the same device ends the older one with None. With 16 devices waiting, the 17th poll gets `too_many_polls`. Revoking all devices raises `device_revoked` in every waiting poll and `_active_polls` returns to 0.

## V01 findings
- LOW-1 RESOLVED (`remote_control.py` `_next_command`):
  - The per-device generation counter is bumped under the Condition, with `notify_all`.
  - The older poll returns None on its next check. Commands are popped under the same lock, so no command can be delivered twice.
  - `_active_polls` is decremented in a `finally` block, so the counter stays correct on revoke, close and exceptions.
  - Residual: the cap check runs before the device's own older poll is superseded. With 16 polls already waiting, a re-poll from one of those devices is refused rather than replacing its older poll. The phone retries after 3 s. Acceptable.
- LOW-2 RESOLVED:
  - `_record` only queues entries under the hub lock. `_flush` swaps the queue under the lock and then writes under a separate `_file_lock`.
  - Rotation uses `os.replace` to a single `.jsonl.1`, which bounds the log at about 2 MiB.
  - Residual: concurrent flushes may write entries out of order (each entry carries `at`).
  - Residual: an OSError in `_flush`, called from a `finally`, would replace the result of `next_command`. A delivered command would then be lost to the phone; it expires and Studio can reissue it. Edge case only.
- LOW-3 RESOLVED: `enabled` is no longer persisted, so control starts off on every launch. The UserDefaults key and its reset line were removed.
- LOW-4 RESOLVED: Finish scan now asks for confirmation with `QMessageBox.question`. It uses a test seam and has a test.
- LOW-5 RESOLVED: `core/src/packlab_core/remote_capture_control.py` and its test were deleted. Outside coordination and TASKS history, the module name appears only in a doc note about the deletion. No imports remain.

## Verdict
CLAUDE_PEER_AUDITED_PASS (security) for PR #21. No new findings above informational. Physical iPhone 16 behaviour remains EXTERNAL_PENDING_REVIEW, and public/factory release remains blocked.
