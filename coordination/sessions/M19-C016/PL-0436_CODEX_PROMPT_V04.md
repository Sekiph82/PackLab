# PL-0436 Codex Prompt V04 — Wire the Verified Workspace Seams

Date: 2026-10-23  
Owner authorization: continue the already-approved local VGGT work. VGGT/Hugging Face access and checkpoint local-use approval are complete; do not ask again. V04 wires the model-independent V03 seams to an injected runtime contract. It does not run or load the checkpoint.

## Objective

Provide an executable, testable workspace adapter that passes verified source images to an injected inference engine, normalizes its camera results, publishes its artifacts through the safe V03 publisher, and returns the existing PackLab reconstruction manifest contract.

## Allowed scope

- Extend `core/src/packlab_core/neural_reconstruction.py` with an injected workspace-engine protocol, immutable camera/inference result records, and a runtime adapter composed from the V03 resolver, coordinate converter, and publisher.
- Extend `tests/core/test_neural_reconstruction_backend.py` with synthetic engine cases only.
- Update this session's V04 criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.
- No upstream source edits, downloads, model weights, application/UI changes, or unrelated cleanup.

## Hard constraints

- Never load, instantiate, or execute VGGT or the 5 GB checkpoint in this task. Synthetic injected engines may produce in-memory matrices and small fixture artifacts only.
- The adapter must fail before invoking the engine when source digest resolution fails, honor cancellation, preserve image order, bind output to project/input identity, retain non-authoritative scale and authority, and keep local paths out of portable metadata.
- Do not silently accept missing, extra, duplicate, non-finite, or misordered camera records. Derived files must pass through `publish_vggt_artifacts`.
- No Actions/paid CI, PR, source push to `main`, native OCCT/OCP or Installer build. Preserve all existing dirty owner changes and avoid a worktree unless required.

## Validation

Run the focused neural IO/backend tests, targeted Ruff, JSON/job-log hash validation, and `git diff --check`. No full suite or model inference.
