# PL-0034 Codex Remediation Log V02

- Cycle: M01-C001
- Task: PL-0034 — CUDA capability provenance remediation
- Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_V01.md
- Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_PROMPT_V02.md
- Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_CRITERIA_V02.md
- Synchronized start: `b3879558c7bf6c7252d9bba519be790e9b40394d`; `HEAD...origin/main` was `0 0`.
- Implementation/evidence commit: `94afd4928249da760f814085f21f62deba7a087e`

## Defect-to-fix mapping

The V01 audit found that the `cuda` capability was based on `nvidia-smi --version`, promoting NVIDIA driver/NVML evidence into CUDA availability. The registry now exposes `nvidia_driver` from `nvidia-smi` separately and probes `cuda` only with `nvcc --version`. CUDA is `AVAILABLE` only when output explicitly identifies CUDA compilation tools or a CUDA toolkit and contains a version; missing direct evidence is `UNAVAILABLE`, probe failure is `UNKNOWN`, and malformed/non-CUDA output is `UNKNOWN`.

No GPU name, memory, AdapterRAM, generic version token, or mere NVIDIA adapter presence is used to claim CUDA. The Python OpenCascade binding remains deliberately unselected and missing/error isolation remains intact.

## Changed files

- `core/src/packlab_core/capabilities.py`
- `tests/core/test_capabilities.py`

## Validation

Expected results and failure conditions:

- `uv run pytest -q tests/core/test_capabilities.py` — expected missing, malformed, direct-CUDA, driver-only, OpenCascade, and generic capability tests to pass. Actual: `7 passed`.
- `uv run ruff check core/src/packlab_core/capabilities.py tests/core/test_capabilities.py` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src/packlab_core/capabilities.py` — expected no type errors. Actual: `Success: no issues found in 1 source file`.
- `uv run pytest -q` — expected sibling M01 regressions to remain green. Actual: `39 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — expected no type errors. Actual: `Success: no issues found in 9 source files`.
- `git diff --check` — expected no whitespace errors. Actual: passed.
- `git diff -- TASKS.md` — expected empty. Actual: empty.
- Exact changed-file review — expected only two authorized files. Actual: only those two files changed.
- Protected/privacy review — expected no secrets, private scans, signing material, cache, or generated artifacts. Actual: passed.

The focused tests would fail on the pre-remediation implementation because NVIDIA-SMI-only evidence previously made `cuda` available. Direct `nvcc` evidence now produces `AVAILABLE` with explicit provenance, while missing and malformed probes stay conservative.

## Scope and platform limitations

Only PL-0034 capability source/tests changed. No M02 work or tracker edit occurred. This Windows run used injected probe results; no native CUDA installation, GPU, driver, or compute-capability claim was fabricated.

## Remote evidence and handoff

Implementation push completed to `origin/main`. After fetch, `HEAD` and `origin/main` resolved to `94afd4928249da760f814085f21f62deba7a087e` with divergence `0 0`.

AWAITING_AUDIT
