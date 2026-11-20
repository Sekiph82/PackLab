# CLAUDE_PEER_REVIEW - Studio package families (PL-0459) - V02

- Reviewer: independent Claude Code peer reviewer (not the builder; no source edited)
- PR #17 head `f094f771a51828a0c76b64247547999d34413123` (re-review of V01 at `10ae7979`; incremental diff reviewed in full)
- Verdict: **PASS** (CLAUDE_PEER_AUDITED_PASS for the source/test scope of PL-0459)

## Evidence I produced myself
- CI run 44838037509: completed/success, headSha f094f771 (verified with gh).
- Scratch `git archive` of the head with a locked offline uv env, run offscreen. Tests run: test_cad_boolean, test_cad_parametric_handle_and_loft, test_cad_step_roundtrip, test_cad_step_export, test_jerrycan_handle_opening, test_package_families, test_labels*, test_project*. Result: 88 passed, 1 skipped.
- I ran the head's `tests/core/test_cad_boolean.py::test_handle_opening_cut_is_deterministic_and_feature_linked` against main's core source, and it FAILS there. So the M1 regression assertion discriminates and is not tautological.

## V01 findings
- **M1 resolved.** `tests/core/test_cad_boolean.py:72-92` asserts a removed volume of 0.84 (rel 1e-6), classifier OUT at x 0.02/0.5/0.98 and IN outside. This matches my V01 probe. The evidence note `PL-0293_CAPTURED_HANDLE_CUT_BOUNDS_EVIDENCE_NOTE_PL0459.md` is accurate. It edits no accepted audit and correctly says operation_id is unchanged while the BREP digest/revision changes.
- **M2 resolved.**
  - `package_families.py:713-720, 795-797` persist `build_mode` and `brep_geometry_sha256` per part.
  - `_verified_reload` (`:1637-1668`) compares (operation_id, build_mode, brep_revision_id) per part name. brep_revision_id already includes the geometry digest.
  - The fitted-jerrycan path is covered too.
  - The test changes the stored loft mode and the BREP id (the latter from a real smooth loft whose operation id is identical) and checks reload refuses both. These are real negatives.
- **L1 resolved.** `labels_view.py:281-289` shows a clear unsupported-family message before any core parse. The test asserts the message and the family label.
- **L2 resolved.** The closure test asserts the exact refusal `neck_section_quality_invalid`, an unchanged revision, the same cap and disabled undo. The success path stays in the dense-fixture undo/redo test.
- **L4 resolved.** `cad_boolean.py:285-286` restricts `body_feature_id` to BODY features. A negative test is added.
- **L3 and L5 unchanged.** Both are accepted as documented limits.

## New observations (LOW, non-blocking)
- **N1.** The new reload check also rejects family documents saved before this change, because `build_mode` is missing. That includes the `10ae7979` evidence-harness project copies. The branch is unreleased, so this is acceptable. Do not present those older project folders as reopenable.
- **N2.** The real-window screenshots/checks.json were produced at `10ae7979`, not at `f094f771`. The changes since then only add records/checks and a Labels message, plus the BODY check; geometry is unchanged. They remain representative, but the Labels screenshot 09c now shows outdated text.

## Gates
mm_unverified, DEFERRED_OWNER_VALIDATION, `mold_use_authorized=false`, the no-claims flags for thread/seal/interference, captured refusal of the parametric cut and disabled pouch export are all unchanged. No physical, factory, iPhone or signing gate is touched.
