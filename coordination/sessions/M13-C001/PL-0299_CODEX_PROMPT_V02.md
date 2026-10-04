# PL-0299 - Codex Work Order V02

Task: **Export OBJ and GLB from one exact Design Model/CAD preview source with stable naming**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001-R01
Branch: `main`

Master continuation:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_PL0299_CONTINUATION_CODEX_PROMPT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CHATGPT_AUDIT_CRITERIA_V02.md

Required V02 log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_LOG_V02.md

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/M13-C001_CHATGPT_PARTIAL_AUDIT_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001-R01 / PL-0299 V02 / CODEX. Re-read M13 master, M13 partial audit, PL-0296 accepted implementation, M12 assembly-hierarchy metadata contract, ADR-0005 and M09 physical deferral. Synchronize safely; preserve owner-local work; no reset/clean/rebase/force-push.

Mandatory pre-reads:

- `core/src/packlab_core/cad_preview.py`
- `core/src/packlab_core/cad_brep.py`
- `core/src/packlab_core/cad_feature_map.py`
- `core/src/packlab_core/assembly_hierarchy_export.py`
- `coordination/sessions/M13-C001/PL-0296_CODEX_PROMPT_V01.md`

## Authority resolution

The M12 assembly-hierarchy handoff is **metadata-only**. It is not authorized as a geometry source for PL-0299.

Do not create multipart/assembly geometry by:

- copying or inventing component meshes from metadata;
- treating hierarchy nodes as embedded geometry;
- inferring component geometry from names/revision IDs;
- silently composing placements without exact component geometry sources.

### Mandatory V02 scope

Implement deterministic export of **one exact Design Model/CAD preview source at a time** to:

1. OBJ
2. GLB

The source must be an exact M13 `CadPreviewMeshRevision` or another already-accepted exact tessellated CAD representation with equivalent provenance. Preserve:

- exact source Design Model revision;
- exact CAD BREP revision/digest;
- exact parent-authority kind/revision;
- coordinate unit and scale state;
- stable semantic part name;
- feature/part mapping where supported;
- physical-validation status and `mold_use_authorized=false`.

OBJ may retain source coordinates directly.

GLB may use a format/viewer-space scale or axis transform only if the transform is explicit, deterministic and reversible in metadata. No transform may upgrade authority.

### Unit rules

- RELATIVE/reconstruction_units is allowed for OBJ/GLB only when explicitly labeled as relative.
- mm_unverified is allowed and remains physically unverified.
- No RELATIVE -> mm promotion.
- No physical/mold/manufacturing claim.

### Assembly behavior

Assembly/multipart export is **not mandatory in PL-0299 V02**.

If the existing metadata-only assembly hierarchy is supplied where geometry is required, fail closed with an explicit error such as `assembly_geometry_source_not_available`.

Do not introduce a new assembly geometry authority contract in this child.

## Required tests/evidence

At minimum cover:

- deterministic single-part OBJ;
- deterministic single-part GLB;
- stable semantic part/node naming;
- exact model/BREP/preview revision propagation;
- RELATIVE OBJ/GLB with explicit relative metadata;
- mm_unverified OBJ/GLB with unverified metadata;
- GLB transform metadata round-trip/reversibility;
- basic OBJ parser/structural check;
- basic GLB header/JSON/buffer parse;
- stale source revision rejection;
- metadata-only assembly handoff rejected as geometry source;
- no Scan Master/Design Model/CAD authority replacement.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and V02 log-only commits. V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0300 under the continuation master. Do not wait for intermediate ChatGPT audit.
