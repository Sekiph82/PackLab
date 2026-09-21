# PL-0024 Codex Remediation Log V02

- Cycle: M01-C001
- Task: PL-0024 — Environment diagnostics GPU discovery remediation
- Original audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_V01.md
- Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V02.md
- Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_CRITERIA_V02.md
- Synchronized start: `d5871da41fe566100c209efa5364a6d3520d1ef9`; `HEAD...origin/main` was `0 0`.
- Implementation/evidence commit: `9ea5d7d357229861809336a6cb89091b1da768fe`

## Defect-to-fix mapping

The V01 audit found that `gpu.adapters` was populated only from `nvidia-smi`, so a Windows host with Intel Iris Xe and no NVIDIA utility reported no adapter. The remediation adds bounded OS-specific adapter discovery: Windows PowerShell/WMI `Win32_VideoController` names, macOS `system_profiler` JSON, and Linux `lspci` display-controller output. Adapter metadata is now separate from NVIDIA driver evidence and CUDA evidence. `nvidia-smi` reports driver evidence only; CUDA is `available` only from a direct `nvcc --version` probe and otherwise remains `unknown`.

The implementation preserves `shell=False`, two-second probe timeouts, no installation or system mutation, deterministic missing/error/unsupported states, structured JSON, and privacy omissions. Generic adapter parsing never reads or converts `AdapterRAM`, GPU memory, adapter presence, or GPU names into CUDA, dedicated VRAM, or compute capability claims.

## Changed files

- `tools/environment_report.py`
- `tests/tools/test_environment_report.py`

## Validation

Expected results and failure conditions:

- `uv run pytest -q tests/tools/test_environment_report.py` — expected all focused tests pass; failure means adapter discovery, CUDA separation, missing-probe, or privacy coverage regressed. Actual: `5 passed`.
- `uv run ruff check tools/environment_report.py tests/tools/test_environment_report.py` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy tools/environment_report.py` — expected no type errors. Actual: `Success: no issues found in 1 source file`.
- `uv run pytest -q` — expected the existing M01 Python suite remain green. Actual: `25 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — expected no type errors. Actual: `Success: no issues found in 9 source files`.
- `git diff --check` — expected no whitespace errors. Actual: passed.
- `git diff -- TASKS.md` — expected empty. Actual: empty.
- Exact changed-file review — expected only the two authorized files. Actual: only those two files changed.
- Protected/privacy review — expected no tracker edit, secrets, private scans, supplier material, credentials, paths, or unsafe generated output. Actual: passed.

Focused injected coverage includes a non-NVIDIA Windows Intel Iris Xe adapter, NVIDIA metadata with missing `nvcc` proving CUDA remains `unknown`, missing probes, deterministic privacy fields, and the no-shell command boundary. The first test-file patch contained an accidental patch marker; it was removed before validation and commit. No unresolved failure remains.

## Scope and platform limitations

Only the authorized PL-0024 implementation and test files changed. No M02 work, task-tracker edit, dependency installation, system mutation, GPU driver change, or native/device claim was made. Windows adapter discovery is represented through a safe PowerShell command array but native host output was not fabricated; injected tests provide deterministic evidence on this checkout.

## Remote evidence and handoff

Implementation push completed to `origin/main`. After fetch, `HEAD` and `origin/main` resolved to `9ea5d7d357229861809336a6cb89091b1da768fe` with divergence `0 0`.

AWAITING_AUDIT
