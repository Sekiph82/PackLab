# PL-0436 Codex Prompt V05 — Memory Admission Before VGGT Runtime

Date: 2026-10-23  
Owner VGGT/Hugging Face access and local checkpoint-use approval are complete. This task uses the owner's current Task Manager screenshots only as resource evidence; it does not run or load the model.

## Objective

Add a fail-closed physical-memory admission layer so a future concrete VGGT engine cannot be entered when the checkpoint plus its configured inference reserve exceeds currently available RAM.

## Allowed scope

- Add `core/src/packlab_core/neural_reconstruction_runtime.py` containing a platform-neutral budget/snapshot contract, a Windows available-memory reader, and a decorator for `VGGTWorkspaceEngine` that checks checkpoint identity by expected file size and available RAM before delegating `infer`.
- Add focused synthetic tests in `tests/core/test_neural_reconstruction_runtime.py` using injected memory readers and fake engines.
- Update this session's V05 criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.

## Hard constraints

- Do not import, instantiate, or execute VGGT/PyTorch; do not read checkpoint bytes, access Hugging Face, or download anything.
- The configured inference reserve is an explicit operator setting. Passing the guard is a minimum resource gate, not proof that inference will succeed or a model-specific benchmark.
- If the checkpoint is missing/wrong-sized, memory measurement fails, or available RAM is below the configured floor, reject before calling the wrapped engine.
- Preserve the owner-authorized local-use state; do not reclassify resolved notices as a pending access/license approval.
- No Actions/paid CI, PR, push to `main`, native OCCT/OCP or Installer build. Preserve owner changes and avoid worktrees unless needed.

## Validation

Run focused runtime/IO/backend tests, targeted Ruff, job JSON/log hash validation, and `git diff --check`. No model inference or full suite.
