---
coordinationSchema: packlab-coordination/v1
artifactType: claude-implementation-log
cycleId: M17-C001
version: 01
actor: CLAUDE_CODE
status: IMPLEMENTED_REVIEW_PENDING
tasks: [PL-0380]
---

# Claude Implementation Log V01 — PL-0380 interrupted COLMAP/OpenMVS job resume/retry

Codex `PL-0380_CODEX_LOG_V01.md` was BLOCKED: the orchestrator always restarted at stage 1, so criterion 2
("retry resumes only from validated checkpoints and preserves completed immutable artifacts") could not be met
by a test alone.

## Change

`core/src/packlab_core/reconstruction_orchestrator.py`:
- `StageCheckpoint(execution, configuration_digest, source_digest)`.
- `ReconstructionOrchestrator.run(..., resume_from=(), verify_checkpoint=None, on_checkpoint=None)`:
  `on_checkpoint` receives each newly verified stage; `resume_from` reuses a prefix only if every checkpoint is in
  stage order, matches this request's configuration and source digests, is a verified SUCCEEDED execution with output
  IDs, and passes `verify_checkpoint` (caller confirms artifacts still exist unchanged). Any mismatch raises; there is
  no silent restart. Reused stages keep their original output asset IDs in the final manifest. Failed/cancelled runs
  still expose no output.

## Tests (`tests/core/test_reconstruction_orchestrator.py`, fake stages, no real compute)

- Interrupted run (crash in stage 3) → FAILED, no output, two checkpoints emitted.
- Retry with checkpoints → stages 1–2 not re-executed, verifier called for each, stages 3+ run, SUCCEEDED manifest
  keeps stages 1–2 asset IDs.
- Rejections: no verifier, verifier False, out-of-order prefix, different configuration digest, different source
  digest, unverified execution.
- Failed resume attempt exposes no partial output.

Result: 10 passed (whole module). ruff/format/mypy clean.

## Limits

Studio wiring (persisting checkpoints through `RecoveryManager` and offering resume in the UI) is not part of this
change; the orchestrator contract is what criterion 2 requires. No COLMAP/OpenMVS binaries were run.
