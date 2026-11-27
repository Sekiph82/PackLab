# CLAUDE_PEER_REVIEW: PR #38 build throughput (V01)

Head d205d05a vs origin/main. Reviewer did not author the change. Tests (worktree PYTHONPATH, offscreen): tests/studio 441 passed, 3 skipped; test_reconstruction_execution 2 passed (needs tests/core on the path, an existing setup issue). COLMAP was not run.

**MEDIUM**
- build_model.py:693: stage `configuration` uses `determinism(self.cpu_share)`, which defaults `max_concurrent_builds=1`. The job spec (line ~911) records the real limit, so one build's provenance contradicts itself. Pass the same `recorded` dict.

**LOW**
- canonicalize_image_ids is correct for this layout: one transaction with rollback, an offset so no primary-key clash, and it refuses to run when matches, two-view, pose_priors or rig_sensors rows exist. Its test uses a hand-built schema rather than a real 4.2.1 database. Real-schema parity comes only from the implementer's report.
- With 4 builds, threads add up to 16+8+5+4, about 2.1x the cores, not the 1.5x stated.
- Scans with GPS tags (pose_priors rows) fail closed with a generic error. PackScan does not write GPS, so current scans are not affected.
- A cancelled job still in the queue briefly takes a slot and counts toward the core split.
- There is no end-to-end timing for the 81-photo scan.

Queue, duplicate handling, UI-thread job calls, per-revision workspaces and the Settings value saved across restarts are all sound. PL-0463 claims are preserved: mapper on 1 thread, fixed seeds, and matching and OpenMVS still documented as not repeatable.

**Verdict: CHANGES_REQUIRED** (the MEDIUM provenance fix only).
