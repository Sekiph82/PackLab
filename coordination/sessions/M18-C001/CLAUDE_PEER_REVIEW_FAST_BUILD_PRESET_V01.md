# CLAUDE_PEER_REVIEW: PR #40 Fast build preset (373c1c71) V01

Independent reviewer, not the author. Local: 33/33 passed. The 3-build test passed 6/6 runs at about 0.7 s. CI runs 46033652192 and 46065764867 passed.

**HIGH**: none.

**MEDIUM**
- Fast and High differ by 20 mm (height) and 24 mm (lid), with no ground truth. Fast accuracy is NOT_VERIFIED. Keep the physical gates open.
- build_model.py:218: RING_SIZE 16 is anchored at index 0, so the same-wedge window is only +15..+17. Retakes or skips push later rings out of it. Without photos.json, name order uses the same ring logic. There is no fallback to exhaustive matching and no test.
- test_build_model.py:139: a 20 s timeout on a 0.7 s test means a hang or a failed job. `_pump` waits only for SUCCEEDED. Stop on any terminal state and assert with the failure reason.

**LOW**
- Nothing tests reading photos.json through the controller, and nothing tests that QSettings `build/quality` survives a restart.
- The UI does not show which preset built a model.

Checked OK: 1165 pairs, ring wrap, NNNN_ names traceable, deterministic, scene_dense_mesh.ply consumers, provenance.

**Verdict: PASS** (MEDIUM follow-ups).
