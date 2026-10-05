# PL-0326 - Codex Blocker Log V01

Task: **Import Design Model, materials and artwork into render scene**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and preflight

- M14-C001-R02 authorizes ordered continuation through PL-0331; PL-0326 follows PL-0325. Root `TASKS.md` was not edited. M15+ remains unauthorized.
- Read the exact PL-0325 predecessor prompt/criteria, PL-0326 prompt/criteria, live R02 continuation prompt/log, and current PL-0325 package source. M13-C001-R02 final audit, M09 physical-validation decision and ADR-0005 were reviewed as part of the PL-0324 pre-read and rechecked during the PL-0325 handoff.
- Starting SHA: `f28e2ff3057e87eebf9f62aba06f80dd175c39db`; branch `codex/m13-c001-pl0297`; local worktree was clean and matched `origin/main` before the blocker review. Push target remains `origin/main`; protected Desktop checkout untouched.
- No PL-0326 implementation or test files were changed. No implementation PASS is claimed.

## Mandatory source-authority blocker

PL-0326 requires real scene import, stable component/part mapping, component material assignment, and front/back/wrap artwork mapping using the accepted scene package. The published upstream contracts do not carry the required stable mappings:

1. `core/src/packlab_core/cad_preview.py` marks every mapped feature's triangle indices as the entire output triangle set and sets mapping scope to `whole_output_solid_preview` (lines 186-197). This explicitly does not identify per-component triangle subsets.
2. `core/src/packlab_core/cad_mesh_export.py` serializes feature IDs/status/reference/scope but omits triangle membership (lines 184-194). Its GLB writer creates one node, one mesh and one primitive; the only vertex attribute is `POSITION`, with no UV coordinates or component material slots (lines 421-440). Stable per-component material assignment cannot be recovered from this fused whole-solid mesh without inventing a partition.
3. The PL-0325 package's `BlenderArtworkBinding` and artwork manifest record contain the exact zone/placement/mapping/artwork revisions, normalized boundary and surface-frame labels (`core/src/packlab_core/blender_scene_package.py`, lines 72-78 and 334-390). They do not contain a host-to-mesh transform, exact surface origin/center, or mesh UV binding.
4. The accepted PL-0313 `LabelMetricSurfaceBinding` persists exact host width/height and mapping parameters such as frame/orientation, but no host placement transform (`core/src/packlab_core/label_metric_surface_binding.py`, lines 30-89). The source BREP is an opaque runtime handle, is not part of the accepted scene package, and the PL-0326 prompt authorizes consuming that package rather than changing upstream CAD/metric authority contracts.

A metadata-only assignment to the whole object would not prove component ownership. Guessing face ownership, manufacturing UVs from whole-solid bounds, persisting transient face identity, or guessing artwork placement would violate the exact-source and fail-closed requirements. The real Blender 5.2.2 capability gate passed at PL-0324, but Blender availability cannot supply missing source mappings.

## Required owner/authority resolution

PL-0326 can resume after an authorized source-contract/prompt update supplies one of these explicit inputs:

- deterministic component-to-mesh primitive/material-slot or triangle-subset mapping, tied to the exact CAD export; and
- exact Label Zone-to-mesh placement/UV mapping for planar and cylindrical-wrap hosts, tied to the exact BREP/metric-binding revisions; or an explicitly authorized separate-overlay contract that does not claim attachment or physical fit.

This is an upstream contract/scope decision. PL-0326 V01 is stopped without product edits; PL-0327 through PL-0331 were not started. No test, Blender import, render, or scene-construction PASS is claimed.

BLOCKED_AUTHORITY