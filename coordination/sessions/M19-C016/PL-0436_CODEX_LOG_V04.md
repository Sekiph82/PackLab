# PL-0436 Codex Log V04 — Injected Workspace Runtime

> Privacy redaction (2026-11-04): machine-specific absolute checkout/TEMP paths in this log were replaced with generic labels; command results and measured values are unchanged. See PL-0436_LOG_PATH_REDACTION_ADDENDUM_V01.md.


Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authority

- Starting commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; final source commit remains the same (no commit created).
- Checkout: `[owner-specific PackLab Desktop path redacted]`, branch `main`. `git fetch origin main` completed; `HEAD == origin/main`, ahead/behind `0/0`. Existing dirty PackLab files were present; no reset, stash, clean, checkout, or unrelated overwrite was done.
- Active task prompt/criteria: `PL-0436_CODEX_PROMPT_V04.md` and `PL-0436_VALIDATION_CRITERIA_V04.md`.
- Mandatory pre-read `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` was reread in full. V03 implementation and its log were reviewed.
- Owner VGGT/Hugging Face access and local checkpoint-use approval are complete. No access request or repeat owner approval was made. No checkpoint, model, or upstream download was accessed in V04.

## Files changed for V04

- `core/src/packlab_core/neural_reconstruction.py`: added `VGGTWorkspaceRuntime`, `VGGTWorkspaceEngine`, and immutable camera/inference result contracts. The runtime resolves exact-digest assets in caller order before the injected engine, normalizes camera transforms, writes portable camera metadata, and uses the V03 atomic derived-output publisher. It fails closed for mismatched camera IDs, invalid geometry counts or scale types, and never publishes when cancellation is observed.
- `tests/core/test_neural_reconstruction_backend.py`: added small synthetic injected-engine tests for ordered input/output metadata, normalized camera pose, digest rejection before engine invocation, malformed camera rejection, cancellation cleanup, and invalid scale rejection.
- This log, V04 prompt/criteria, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json` record task status and evidence.

## Validation

1. Command: `.\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: targeted synthetic IO/backend tests pass without loading any model; nonzero exit is failure.
   - Actual: **19 passed, 1 skipped** (exit 0). The skip is Windows symlink creation capability. During iteration, two assertions had incorrect expected pose/error detail; corrected assertions then passed. A later invalid-scale guard/test was added and the final run remained green.
2. Command: `.\.venv\Scripts\ruff.exe check core/src/packlab_core/neural_reconstruction.py core/src/packlab_core/neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py tests/core/test_neural_reconstruction_io.py`
   - Expected: no diagnostics.
   - Actual: **All checks passed!** (exit 0).
3. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0; existing LF-to-CRLF working-copy warnings only.

## Resource, safety, and limits

- No VGGT runtime or checkpoint weights were imported, loaded, or executed. The workspace engine remains an injected protocol; V04 proves only local adapter wiring with synthetic fixtures.
- Real inference still requires a concrete supported engine and sufficient physical RAM. No PackScan parity, real-image inference, physical ground truth, metric scale, hosted verification, independent review, or release readiness is claimed.
- Resolved runtime dependency notices and end-user AUP/license delivery are distribution packaging work; owner access/local-use approval is complete, not pending.
- Zero Actions/paid CI; no PR; no source push to `main`; no native OCCT/OCP or Installer build. `NO_LOCAL_WORKTREE_CREATED`; no dashboard used. No credentials or private owner data added.

## Handoff

`LOCAL_INJECTED_WORKSPACE_RUNTIME_WIRED_AND_SYNTHETIC_TESTED_OWNER_ACCESS_APPROVED_REAL_INFERENCE_PENDING_CONCRETE_ENGINE_AND_SUFFICIENT_RAM_NO_RELEASE_CLAIM` — verified input/output/coordinate boundaries are now composed behind an injected PackLab runtime contract. Actual model inference remains unperformed pending a concrete engine and adequate measured memory.
