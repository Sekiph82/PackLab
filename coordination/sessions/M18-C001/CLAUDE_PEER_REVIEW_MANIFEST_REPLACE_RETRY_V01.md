# CLAUDE_PEER_REVIEW: PR #48 manifest replace retry (V01)

Head 01eb0199 vs main.

HIGH: none.

MEDIUM: none.

LOW:
- The retry makes the race unlikely, not impossible. In a stress run with a reader in a tight loop, `os.replace` failed 848 of 2000 times before the change and 3 of 2000 after it. A lock (see `provenance.py:38-41`) would rule it out.
- A real permission denial now waits about 1.6 s before it is raised. The error still surfaces; the wait is on the build thread (`build_model.py:1030-1129`), not the UI thread.

Checked:
- Root cause: the UI calls `latest_builds()` after every job change (`build_model.py:1357,1407`).
- No other writer of workspace `manifest.json`.
- The temp file is deleted in `finally`, and none were left.
- The test still requires SUCCEEDED, so it can still fail.
- 40 runs from the worktree: 40 passed.

Verdict: PASS. PR CI was still pending, so it is NOT_VERIFIED.
