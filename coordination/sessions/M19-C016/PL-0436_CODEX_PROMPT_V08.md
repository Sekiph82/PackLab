# PL-0436 Codex Prompt V08 — Isolated Offline VGGT Worker

Date: 2026-10-23  
Owner VGGT/Hugging Face access and local checkpoint-use approval are complete. The checkpoint and upstream code revisions are pinned; local SHA verification is complete. V08 wires the already-prepared streaming loader into a concrete, isolated CPU worker without executing inference during this task.

## Objective

Implement a subprocess-backed VGGT workspace engine that accepts verified PackLab images, uses only the pinned local code/checkpoint/runtime, and returns camera predictions plus a bounded point-cloud artifact. The caller's existing lazy engine factory must remain behind the physical-memory admission guard. The worker must be offline and must never download model files.

## Allowed scope

- Add `core/src/packlab_core/vggt_worker.py` as a CLI worker using the pinned upstream VGGT APIs and `load_safetensors_into_cpu_model`.
- Add `VGGTSubprocessWorkspaceEngine` and its narrow process/protocol helpers to `core/src/packlab_core/neural_reconstruction_runtime.py`.
- Add an explicit opt-in cleanup marker to `VGGTOutputArtifact`; clean only engine-created artifacts under the configured runtime output root, on success, cancellation, or failure.
- Add focused synthetic tests for worker request/result validation, process cancellation/failure, and cleanup. Tests must not instantiate VGGT or read the real checkpoint.
- Add/update this V08 prompt, criteria and log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.

## Hard constraints

- Do not run the worker against the real checkpoint or run inference in V08. This Windows host's latest measured available physical RAM is below the checkpoint size; the RAM gate must continue to reject before engine construction.
- Worker verifies the exact pinned upstream code revision, checkpoint size/SHA and each input image digest before use. It must set Hugging Face/Transformers offline flags and must not invoke hub download helpers.
- The worker runs CPU-only, loads a fresh model with the streaming safetensors helper, and returns no private absolute paths in serialized results/errors.
- Bound input/result JSON sizes, process lifetime, point count and output size. Reject malformed JSON, non-finite matrices/points, non-regular/reparse output paths, unexpected image/camera order, and bad exit status.
- Never delete arbitrary files. Only remove uniquely created temporary request/result directories and artifacts explicitly marked task-generated and verified beneath the runtime output root.
- No GitHub Actions/paid CI, PR, source push to `main`, OCCT/OCP or Installer build, dashboard, checkpoint download, or extra package installation. Preserve all pre-existing owner changes and do not modify unrelated files.

## Validation

Use small synthetic worker/protocol tests and focused PackLab runtime/IO/backend tests. Run targeted Ruff where available, validate task JSON/log SHA-256 and `git diff --check`. Record the exact live RAM reading and explicitly confirm no real model/checkpoint/inference execution. Stay local; final runtime readiness and release claims remain out of scope.
