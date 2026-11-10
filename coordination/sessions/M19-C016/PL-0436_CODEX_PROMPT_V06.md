# PL-0436 Codex Prompt V06 — Lazy Engine Construction After Resource Admission

Date: 2026-10-23  
Owner VGGT/Hugging Face access and local checkpoint-use approval are complete. This version closes a safety gap in the next runtime seam: constructing an engine can import model libraries or load weights, so construction must not precede checkpoint/RAM admission.

## Objective

Add a lazy guarded `VGGTWorkspaceEngine` wrapper that checks the pinned checkpoint metadata and configured available-RAM floor before its factory can run. Capability probing may use an injected lightweight prerequisite probe; it must not construct the engine. Inference must not construct the engine when canceled, when resources fail admission, or when prerequisites report unavailable.

## Allowed scope

- Extend `core/src/packlab_core/neural_reconstruction_runtime.py` with the lazy guarded engine and shared admission logic.
- Extend `tests/core/test_neural_reconstruction_runtime.py` with synthetic fake factories, probes, memory snapshots and engines.
- Update this V06 prompt/criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.

## Hard constraints

- Do not instantiate the actual VGGT model, load/read checkpoint bytes, perform inference, access Hugging Face, or download packages/files.
- Engine factories and prerequisite probes are injected; tests must remain synthetic and may not import torch/VGGT.
- The factory is invoked at most once after a passing resource gate; failed admission, cancellation, and a false/failed prerequisite probe must happen before factory invocation.
- Passing the configured RAM floor does not guarantee inference will fit or succeed.
- Keep owner-approved local VGGT access/use recorded as complete. Do not request repeat approval or describe it as pending.
- No Actions/paid CI, PR, push to `main`, native OCCT/OCP or Installer build. Preserve all pre-existing owner changes.

## Validation

Run focused runtime/IO/backend tests and targeted Ruff; validate the job JSON and V06 log SHA-256; run `git diff --check`. Do not run the full test suite or model inference.
