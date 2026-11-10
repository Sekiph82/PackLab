# PL-0436 Codex Log V05 — Memory Admission Guard

> Privacy redaction (2026-11-04): machine-specific absolute checkout/TEMP paths in this log were replaced with generic labels; command results and measured values are unchanged. See PL-0436_LOG_PATH_REDACTION_ADDENDUM_V01.md.


Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authority

- Starting and final source commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02` (no commit created).
- Checkout: `[owner-specific PackLab Desktop path redacted]`, branch `main`. `git fetch origin main` completed; `HEAD == origin/main`, ahead/behind `0/0`. Pre-existing dirty PackLab changes were preserved; no reset, stash, clean, checkout, or unrelated overwrite.
- Active prompt/criteria: `PL-0436_CODEX_PROMPT_V05.md` and `PL-0436_VALIDATION_CRITERIA_V05.md`.
- Mandatory pre-read `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` was read in full; V04 adapter contract was reviewed.
- The owner-approved VGGT/Hugging Face access and local checkpoint use remain complete, not pending. No model weights were read, instantiated, or executed.

## Resource evidence and implementation

- Owner screenshot shows 16.0 GB installed LPDDR5, 14.4/15.7 GB in use (92%), and 1.3 GB available. A live `Win32_OperatingSystem` read during this turn measured 16,870,006,784 total physical bytes and 405,180,416 free physical bytes. The screenshot's C: capacity/free-space display is storage, not RAM.
- Added `core/src/packlab_core/neural_reconstruction_runtime.py`: validated physical-memory snapshots and explicit checkpoint-plus-reserve budgets, a Windows `GlobalMemoryStatusEx` reader, and `GuardedVGGTWorkspaceEngine`. It uses checkpoint file metadata only and rejects a missing/non-regular/wrong-sized checkpoint, RAM measurement failure, or insufficient available memory before calling the wrapped engine. The configured reserve is a minimum admission floor, not a validated model-specific requirement or inference guarantee.
- Added `tests/core/test_neural_reconstruction_runtime.py`: synthetic memory readers and fake engines cover invalid budgets/snapshots, low-memory rejection before engine invocation, absent/wrong-sized/symlink checkpoint metadata, measurement failure, and a passing floor delegating exactly once. Tests do not open model contents.
- Updated V05 prompt/criteria, `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json` with the memory gate and evidence.

## Validation

1. Command: `.\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: focused runtime, IO, and adapter tests pass using fake engines only; nonzero exit is failure.
   - Actual: **35 passed, 2 skipped** (exit 0). Both skipped cases require symlink creation unavailable in this Windows environment.
2. Command: `.\.venv\Scripts\ruff.exe check core/src/packlab_core/neural_reconstruction_runtime.py core/src/packlab_core/neural_reconstruction.py core/src/packlab_core/neural_reconstruction_io.py tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_backend.py tests/core/test_neural_reconstruction_io.py`
   - Expected: no diagnostics.
   - Actual: **All checks passed!** (exit 0).
3. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0; existing LF-to-CRLF working-copy warnings only.
4. Command: `.\.venv\Scripts\python.exe -B -c "from packlab_core.neural_reconstruction_runtime import WindowsPhysicalMemoryReader; print(WindowsPhysicalMemoryReader().snapshot())"`
   - Expected: a system-wide physical-memory snapshot, with no model import or checkpoint read.
   - Actual: `VGGTMemorySnapshot(total_physical_bytes=16870006784, available_physical_bytes=1547358208)` (exit 0). The snapshot varies over time; both this and the earlier 405,180,416-byte CIM free-memory sample remain below the 5,026,367,224-byte checkpoint size.

## Limits, privacy, and handoff

- No VGGT/PyTorch runtime import, checkpoint content read, inference, download, or model activation occurred. The concrete engine remains unimplemented; the latest Windows available-memory API sample was 1,547,358,208 bytes, still below the 5,026,367,224-byte checkpoint size.
- The admission floor is configurable and conservative only by configuration; it does not claim that passing the floor guarantees CPU inference will succeed. Real model inference and PackScan parity remain unverified.
- Owner access/local-use approval is complete. Runtime notice review and end-user AUP/license presentation are distribution packaging tasks, not pending owner approval.
- Zero Actions/paid CI; no PR; no source push to `main`; no native OCCT/OCP or Installer build. `NO_LOCAL_WORKTREE_CREATED`; no dashboard used. No credentials or private data added. No independent review, hosted verification, physical acceptance, or release-readiness claim.

`LOCAL_MEMORY_ADMISSION_GUARD_IMPLEMENTED_AND_SYNTHETIC_TESTED_OWNER_ACCESS_APPROVED_REAL_INFERENCE_PENDING_CONCRETE_ENGINE_AND_AVAILABLE_RAM_NO_RELEASE_CLAIM`
