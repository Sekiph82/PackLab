# PL-0035 — Codex Remediation Log V03

Task: PL-0035 — Non-destructive Windows process-tree proof remediation  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V03.md  
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_V02.md

## Synchronization and scope

- Root `TASKS.md` authorized `M01-REMEDIATION-BATCH-002` with Required Actor `CODEX` before material work.
- Synchronized start commit: `114264cb7d055aac8ca4fcd5395dfc6571cd896b`.
- `git fetch origin main --prune`, `git rev-list --left-right --count HEAD...origin/main`, and `git status --porcelain` confirmed a clean `0 0` state before edits.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used. `TASKS.md` was not edited and M02 was not started.

## Defect-to-fix mapping

The V02 audit found that the Windows regression used `os.kill(pid, 0)`, which is not a non-destructive Windows liveness proof. The tests now use a PID-scoped `tasklist /FI "PID eq <pid>" /FO CSV /NH` query on Windows and retain `os.kill(pid, 0)` only for non-Windows hosts. A dedicated live-process control test proves the helper observes a live process without terminating it; timeout and cancellation tests use the same helper to prove both runner-owned parent and spawned child are already gone, so parent-only cleanup would fail the regression.

The runner still invokes `taskkill /PID <owned-root> /T /F` with bounded timeout, `shell=False`, and an argument array. It now checks the completion result and returns bounded structured cleanup error evidence through `ProcessResult.error` for nonzero exit, timeout, or start failure, while still attempting safe root termination and bounded fallback kill. POSIX process-group cleanup, streaming callbacks, shell-free execution, argument arrays, and existing result fields remain intact.

## Changed files

- `core/src/packlab_core/subprocess_runner.py`
- `tests/core/test_subprocess_runner.py`

No adjacent files were required. No unrelated process matching or broad termination was added.

## Validation

Expected results: Windows liveness checks must be non-destructive and PID-scoped; timeout/cancellation must prove both processes are gone; taskkill failure modes must be surfaced while the owned root is still stopped; POSIX and existing runner behavior must remain green. The pre-V03 liveness implementation would fail the control/descendant proof because it used the unsafe Windows `os.kill` behavior.

Executed commands and actual results:

- `uv run pytest -q tests/core/test_subprocess_runner.py` — `9 passed`.
- `uv run pytest -q` — `47 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — no issues found in 9 source files.
- `git diff --check` — passed.
- `git diff -- TASKS.md` — empty.
- Exact changed-file review — only the two authorized files changed.
- Privacy/security review — no secrets, private scans, supplier files, signing material, caches, unrelated process matching, or unsafe artifacts added.

The focused suite ran on Windows and exercised the Windows runner branch. No native/device evidence was required or fabricated.

## Publication and handoff

- Implementation/evidence commit pushed to `origin/main`: `20802786bc2b49eb146d78b659d33953632039ec`.
- Post-push `git fetch origin main --prune` completed and divergence was `0 0`.
- This log is published as a separate log-only commit from the implementation/evidence commit.
- No audit verdict is assigned and no future log commit SHA is predeclared.

AWAITING_AUDIT
