# PL-0436 Codex Log V06 — Lazy Resource-Gated Engine

> Privacy redaction (2026-11-04): machine-specific absolute checkout/TEMP paths in this log were replaced with generic labels; command results and measured values are unchanged. See PL-0436_LOG_PATH_REDACTION_ADDENDUM_V01.md.


Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authority

- Starting and final source commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; no commit created.
- Checkout: `[owner-specific PackLab Desktop path redacted]`, branch `main`. `git fetch origin main` succeeded; `HEAD == origin/main`, ahead/behind `0/0`. The checkout already contained extensive unrelated/owner PackLab changes; all were preserved without reset, stash, clean, checkout or overwrite.
- Active task prompt and criteria: `PL-0436_CODEX_PROMPT_V06.md` and `PL-0436_VALIDATION_CRITERIA_V06.md`. The mandatory neural reconstruction implementation pre-read was read in full; V05 code/log were reviewed.
- Owner VGGT/Hugging Face access and local checkpoint-use approval remain complete. No repeated access request was made.

## Implementation

- Added `LazyGuardedVGGTWorkspaceEngine` in `core/src/packlab_core/neural_reconstruction_runtime.py`. It checks the regular-file checkpoint size and configured available-RAM floor before capability probing or engine construction. Its prerequisite probe is injected and lightweight; the engine factory is never called by construction or `available()`, and is called at most once on a non-canceled inference after admission and a passing prerequisite probe.
- Shared checkpoint/memory admission between the existing and lazy wrappers. Factory failures and invalid factory results fail closed with path-free messages. Cancellation returns a canceled inference envelope without taking a memory sample or constructing the engine.
- Added synthetic tests for low-memory admission, probe behavior, cancellation, single lazy construction/reuse, invalid factories, and factory failures. No test imports torch/VGGT or reads model data.
- Live Windows memory API smoke returned 16,870,006,784 total bytes and 3,335,286,784 available bytes. This remains below the 5,026,367,224-byte checkpoint size; the model was not loaded or run.

## Validation

1. Command: `git fetch origin main; git rev-list --left-right --count HEAD...origin/main`
   - Expected: safe sync and no divergence; nonzero fetch exit or nonzero count requires stop.
   - Actual: fetch succeeded; `0 0`.
2. Command: `\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: focused synthetic/runtime regressions pass; nonzero exit is failure.
   - Actual: **42 passed, 2 skipped** (exit 0); both skips require Windows symlink creation unavailable in this environment.
3. Command: `\.venv\Scripts\ruff.exe check core/src/packlab_core/neural_reconstruction_runtime.py core/src/packlab_core/neural_reconstruction.py core/src/packlab_core/neural_reconstruction_io.py tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_backend.py tests/core/test_neural_reconstruction_io.py`
   - Expected: no diagnostics.
   - Actual: **All checks passed**. Initial Ruff run found UP035 (`Callable` import location); moved it to `collections.abc` and reran successfully.
4. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0; only existing LF-to-CRLF working-copy warnings were printed for pre-existing dirty files.
5. Command: `\.venv\Scripts\python.exe -B -c "from packlab_core.neural_reconstruction_runtime import WindowsPhysicalMemoryReader; print(WindowsPhysicalMemoryReader().snapshot())"`
   - Expected: system-wide memory counters only; no model import or checkpoint read.
   - Actual: `VGGTMemorySnapshot(total_physical_bytes=16870006784, available_physical_bytes=3335286784)`.

## Limits, privacy, and handoff

- This version adds only lazy resource-gated engine construction. It does not implement the concrete VGGT inference engine. Current available RAM remains below checkpoint size, so inference did not run; no checkpoint contents were opened, model instantiated, downloads made, or inference executed.
- The configured floor is not an empirical inference threshold and passing it does not guarantee successful inference. Real PackScan parity and physical ground truth remain unverified.
- Owner access/local-use approval is complete. Runtime notices and end-user AUP/license delivery remain distribution packaging work, not pending owner approval.
- Zero Actions/paid CI; no PR; no source push to `main`; no native OCCT/OCP or Installer build. `NO_LOCAL_WORKTREE_CREATED`; no dashboard used. No credentials, private user data, owner Desktop data or OwnerDev files were touched. No independent review, hosted verification, physical acceptance or release-readiness claim.

`LOCAL_LAZY_ENGINE_FACTORY_RESOURCE_GATED_AND_SYNTHETICALLY_TESTED_OWNER_ACCESS_APPROVED_REAL_INFERENCE_PENDING_CONCRETE_ENGINE_AND_SUFFICIENT_AVAILABLE_RAM_NO_RELEASE_CLAIM`
