# PL-0035 Codex Remediation Log V02

- Cycle: M01-C001
- Task: PL-0035 — Windows subprocess process-tree cleanup remediation
- Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_V01.md
- Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V02.md
- Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V02.md
- Synchronized start: `9410a6dd4448e02e43120d93184e6bf1bc8b3e43`; `HEAD...origin/main` was `0 0`.
- Implementation/evidence commit: `d9d6f65409c073b10ad0762824736285773606ee`

## Defect-to-fix mapping

The V01 audit found that Windows first terminated only the direct parent and skipped `taskkill /T` if that parent exited promptly, allowing spawned descendants to survive. The runner now creates Windows children with `CREATE_NEW_PROCESS_GROUP` and, on timeout/cancellation, immediately invokes `taskkill /PID <runner-owned-parent> /T /F` with bounded timeout, `shell=False`, and argument-array scope. It waits for the root process and retains a bounded fallback terminate/kill path. POSIX continues to use the runner-owned process group via `start_new_session=True` and `killpg`.

## Changed files

- `core/src/packlab_core/subprocess_runner.py`
- `tests/core/test_subprocess_runner.py`

## Validation

Expected results and failure conditions:

- `uv run pytest -q tests/core/test_subprocess_runner.py` — expected success/nonzero/stdout/stderr, shell-free, timeout parent-child, and cancellation parent-child coverage to pass. Actual: `5 passed`.
- `uv run ruff check core/src/packlab_core/subprocess_runner.py tests/core/test_subprocess_runner.py` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src/packlab_core/subprocess_runner.py` — expected no type errors. Actual: `Success: no issues found in 1 source file`.
- `uv run pytest -q` — expected sibling M01 regressions to remain green. Actual: `39 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — expected no type errors. Actual: `Success: no issues found in 9 source files`.
- `git diff --check` — expected no whitespace errors. Actual: passed.
- `git diff -- TASKS.md` — expected empty. Actual: empty.
- Exact changed-file review — expected only two authorized files. Actual: only those two files changed.
- Protected/privacy review — expected no secrets, private scans, signing material, cache, or unsafe artifacts. Actual: passed.

The focused regressions launch Python parents that spawn long-lived Python children, record both PIDs, trigger timeout and cancellation separately, join the runner thread, and prove both PIDs disappear. They would fail against the audited pre-remediation path if the parent exited before tree termination.

## Scope and platform limitations

Only the authorized PL-0035 runner and tests changed. No M02 work or tracker edit occurred. The test run executed on Windows and exercised the runner’s Windows branch; no unrelated process matching or broad system termination was used. Native iOS/device evidence is outside this task and was not fabricated.

## Remote evidence and handoff

Implementation push completed to `origin/main`. After fetch, `HEAD` and `origin/main` resolved to `d9d6f65409c073b10ad0762824736285773606ee` with divergence `0 0`.

AWAITING_AUDIT
