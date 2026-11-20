# CLAUDE_PEER_REVIEW - PR #16 studio-history-authority (PL-0456, PL-0447 remainder) - V01

- Reviewer: independent Claude peer reviewer. I did not write this PR. This is not CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Base/head: origin/main 573231eb -> origin/feat/studio-history-authority b5e844fc (6 files, +830/-24).
- Verdict: **PASS_WITH_NOTES** (no HIGH findings).

## Evidence I checked myself
- Read the full diff of project.py, recovery.py, shell.py, measure_view.py and both test files. Also read history.py and the labels-branch reader (design_workbench.py).
- I ran the tests in a detached worktree at b5e844fc, with a venv that has cv2 so the Measure & Design tests are not skipped. Command: test_measure_design, test_recovery, test_history, test_project. Result: **22 passed**. The desktop .venv has no cv2, so test_measure_design gets skipped there.
- I wrote my own temporary probe, which I deleted afterwards:
  (a) I changed the pointer outside history, then called undo(). It returned None and did not overwrite the pointer.
  (b) I appended one byte to the artifact. selected_design_model() then raised "digest mismatch".
  (c) I forced a free-space failure after the file was written. See M1.
- CI run 44821285399 "PackLab Windows Python Quality": completed/success, headSha b5e844fc (checked with gh).
- E2E: I read e2e_log_A/B/C.json and the screenshots B02 (recovery dialog) and B04 (portability report). B shows a resumable draft that is then restored. C shows a clean restart with no dialog, and the selected design is unchanged.

## Findings
MEDIUM
- M1 project.py:553 vs 581. The file is created (create-only) before commit_edit runs its free-space and conflict checks. I confirmed that when the commit fails, an orphan file is left in derived/design_model/. Retrying the same document then fails with "immutable project artifact already exists". Also, `latest_project_design_model` on the labels branch picks the newest file by mtime (design_workbench.py:376-381), so it would pick up the orphan. Fix: run the pre-checks before writing, or reuse an orphan whose bytes are identical.
- M2 Integration. The labels-branch reader ignores `active_design_model_revision_id`, so undo/redo and selection are invisible to it. The file contract and bytes are unchanged (compatible). After merge, the labels branch should switch to `selected_design_model()`. measure_view.py save_design will also conflict with labels measure_view.py:553.

LOW
- L1 project.py:650/695. After undo is refused, can_undo stays True (I confirmed this), so the Undo menu item stays enabled but does nothing.
- L2 shell.py:655-660. A draft is restored even when the checkpoint status is INVALID (digest changed). The dialog still labels the button "Recover".
- L3 Undoing a Scan Master selection can leave the active Design Model fitted to a Scan Master that is no longer selected. measure_view.py:222 refreshes scan_master only when the project switches.
- L4 Not covered by tests: refusal after an outside-history change, digest tamper, and commit failure after the file write. My probes covered these, but no committed test does.

## Clean checks
- Append-only records. Lineage is checked as an ID plus a mesh_sha256 match against a persisted Scan Master. mold_use_authorized must be False, and status must be DEFERRED_OWNER_VALIDATION.
- recovery.mark_start keeps checkpoints only when the status is "active". mark_clean_close still clears them, and the marker is per-project.
- The autosave draft holds only IDs, the review flag and two mm values. It contains no owner data.
- All writes run on the UI thread, but they are small JSON files.
