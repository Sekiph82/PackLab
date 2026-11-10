# PL-0435 Validation Criteria V01 — Offline Visual Reference Boundary

1. Provenance requires generator, model, checkpoint, version, at least one conditioning input, nonnegative integer seed, and canonical JSON-safe settings.
2. Conditioning and artifact/checkpoint identities reject malformed SHA-256 digests.
3. Serialized records always include `generated=true`, `authority_class=AI_VISUAL_REFERENCE`, a persistent invented-geometry caveat, and complete provenance.
4. The record carries no mesh vertices/measurement points and offers no conversion to captured or authoritative geometry; explicit promotion fails closed.
5. The contract imports no model SDK and activates no backend. No model/checkpoint bytes are downloaded or created.
6. Viewport scene kind supports independent visibility from Scan Mesh/Design Model, draws a persistent generated/caveat label while visible, and writes the full provenance record plus `generated=true`, authority, caveat, and visibility into preview sidecar metadata.
7. Removing a visual reference removes only that layer and preserves the exact captured Scan Mesh geometry object.
8. Exact core local validation: `$env:PYTHONPATH='core/src'; python -m pytest -q tests/core/test_visual_reference.py tests/ci/test_codex_task_queue.py`.
9. Exact viewport local validation when existing PySide6 runtime exists: `$env:PYTHONPATH='core/src;apps/windows-studio/src'; $env:QT_QPA_PLATFORM='offscreen'; python -m pytest -q tests/studio/test_visual_reference_viewport.py`.
10. Exact static syntax validation: `py -3.12 -c "import ast,pathlib; paths=['core/src/packlab_core/visual_reference.py','apps/windows-studio/src/packlab_studio/viewport.py','apps/windows-studio/src/packlab_studio/viewport_export.py','tests/core/test_visual_reference.py','tests/studio/test_visual_reference_viewport.py']; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'),filename=p) for p in paths]; print('AST_PARSE_PASS',len(paths))"`.
11. Exact repository hygiene validation: `git diff --check`.
12. No GitHub Actions/paid CI, PR, native rebuild, iOS XCTest claim, or release-readiness claim is allowed.

Passing local checks establish implementation evidence only, not independent audit, model-license clearance, hosted validation, or release readiness.
