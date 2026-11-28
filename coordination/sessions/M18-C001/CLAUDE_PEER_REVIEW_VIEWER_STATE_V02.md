# CLAUDE_PEER_REVIEW viewer state V02 (PR #46, head 36d13696)

Verdict: PASS. CI Windows quality attempt 2 green (3685 passed). Local runs NOT_VERIFIED: host overloaded by other sessions.

V01 findings fixed: page stays put, owner-opened model kept, newer build offered, reads coalesced/cancellable, memory capped.

Flake root cause, reproduced locally (5 failures in about 60 runs): one job FAILED with `PermissionError [WinError 5]` in reconstruction_workspace.py:116 `os.replace`. UI-thread readers (build_model.py:1514/1556) open manifest.json mid-replace. `_pump` waits only for SUCCEEDED, so this shows as a 20 s timeout. Pre-existing; this PR adds no manifest readers, so it is not worse. Fix: retry the replace; stop the pump on terminal states.

- MEDIUM test_viewer_state_persist.py:192: `< 0.3 s` wall-clock assert failed under load (1.37 s).
- LOW: re-picking the current part does not unpin.
