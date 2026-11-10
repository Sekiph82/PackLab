# PL-0424 Validation Criteria V01 — Deterministic Reconstruction Anomaly Proposals

1. Detector binds findings to exact geometry-statistics revision ID and geometry SHA-256; confidence report digest is retained when supplied.
2. Disconnected mesh components, nonmanifold edges, boundary edges, below-profile confidence, and missing/incomplete diagnostic evidence map to documented allow-listed findings.
3. Finding order and report ID are deterministic. Inputs are not mutated.
4. Missing confidence/statistics evidence is marked incomplete/review-required; it cannot produce a clean pass.
5. Serialization contains no mesh/sample bytes or paths; it states diagnostic-only authority, no geometry mutation, no Scan Master replacement and deferred physical validation.
6. Synthetic local fixtures only; no model, private scan, supplier image, network, native build, or AI runtime.
7. Exact local validation: `python -m pytest -q tests/core/test_reconstruction_anomaly.py` with `PYTHONPATH=core/src`.
8. `git diff --check` passes; no Actions, paid CI, PR, main source push, or release claim.
