# CLAUDE_PEER_REVIEW - PR #25 receiver auto-start (V02)
Head 30351904 vs origin/main 185c2dbf. Own findings; reviewer did not author.
Tests: worktree, .venv, offscreen: test_capture_inbox + test_project_menus 13 passed (new test calls resume_paired_receiver, absent on main, so worktree source ran). No probe of the real profile.
- MEDIUM-1 RESOLVED: auto-start only via app.run() non-smoke branch (app.py:214); windows never self-start (test asserts _session is None).
- LOW-1 RESOLVED: issue_code=False, offer None after _tick; lambda keeps clicked(bool) from passing False.
- Shutdown guard tested.
- Open, follow-up: MEDIUM-2 port/IP fallback; no test that build smoke skips resume (LOW).
Verdict: PASS
