# CLAUDE_PEER_REVIEW - PR #26 weak registration refusal (V01)

Reviewed commit 6a2fb35b on base 1b2870dc. Read-only worktree. Reviewer did not write this change.

- Threshold: 0.5 refuses 3/17 and 8/17, passes 9/17. Earlier real builds of 16/20 and 24/28 still pass.
- Error path: build_model.py:488 raises BuildModelError. The orchestrator catches it (reconstruction_orchestrator.py:375) and returns a FAILED result with failure_reason. finish("failed", "Build failed: BuildModelError: only 3 of 17 ...") then calls show_result. The fail-closed job and workspace handling is unchanged. registered_images is set before the raise, so the result still shows 3/17.
- input_images is set in features (:395), which runs before mapping. The existing 'no photos' path is unchanged.
- Tests: 14 passed (test_build_model.py, offscreen). The new test checks both sides of the threshold.
- Low: if input_images is missing, total is 0 and the check is skipped (fails open). No end-to-end UI test.

Verdict: PASS
