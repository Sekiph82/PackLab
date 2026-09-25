# PL-0122 — ChatGPT Remediation Audit V04

Decision: **CHANGES_REQUIRED**

## Independent result

Pairing lifecycle now distinguishes active vs idle; already-idle QR acquisition succeeds without restore, active stop refusal fails, displaced capture is restored conditionally, and wrong-version PairingOffer is tested.

The task-specific V04 remediation is functionally satisfied on final `main`.

However, the frozen M05-BATCH-004 audit criteria state that **all criteria are mandatory**, including criterion 15: the full locked suite must pass truthfully. Codex reports:

- full locked suite: `218 passed, 4 skipped, 1 deselected` plus **1 failure**
- failing test: `tests/core/test_subprocess_runner.py::test_windows_liveness_query_is_non_destructive`
- the same test passes in isolation
- the full suite excluding only that test passes

Because the exact required full-suite gate did not exit cleanly, this child cannot receive `AUDITED_PASS` yet even though its product behavior is otherwise acceptable.

## Required remediation

Do not rewrite this task's product logic unless a regression is discovered. Clear the shared full-suite validation blocker by making the unchanged Windows liveness proof deterministic under aggregate-suite load, then rerun the exact full locked command with zero failures. Preserve all accepted M05 behavior and re-submit batch-level evidence.

PL-0122 remains unchecked solely because the mandatory full-suite gate is not green.

Decision: **CHANGES_REQUIRED**
