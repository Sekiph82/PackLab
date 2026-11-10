# PL-0371 — Codex Prompt V01

Task: **Store dimension and capture-condition provenance for M17 benchmark objects**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

## Scope

- Keep task 0371 metadata in the local M17 dataset manifest and its reproducible generator/extractor; full images and models stay outside Git.
- Store generated mesh dimensions from the serialized PLY and simulated dimensional tolerance inputs. Label them synthetic.
- Store YCB source model identity and source scanner scale separately from independently measured physical dimensions. Do not claim source scanner dimensions are calibrated physical truth.
- Store virtual camera pose/intrinsics, render/light settings and distortion for synthetic views. For YCB photos, state that camera pose/intrinsics and photo-to-mesh registration are unknown/not bound.
- Do not add Kenya field measurements, facility scans or physical acceptance claims.

## Validation timing

- Add fail-closed metadata coverage to the M17 validation suite. Do not run pytest/tester per task; perform the consolidated M17 test and review checkpoint at milestone end.
- Run only the dataset artifact integrity validator needed to confirm generated data/metadata after generation; it is not the full software test batch.
- Write `PL-0371_CODEX_LOG_V01.md` with the exact implementation, evidence, limitations and deferred milestone validation.
