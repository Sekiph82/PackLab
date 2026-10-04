# PL-0313 - Codex Implementation Log V01

Task: **Generate 2D label boundary/dieline in millimetres**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes M14-C001-R01: PL-0312 V02 followed by PL-0313 through PL-0331; status `CHANGES_REQUIRED`; actor `CODEX`. The tracker was not edited.
- Read the R01 continuation prompt/criteria, PL-0313 prompt/criteria, PL-0312 V02 predecessor prompt/criteria, PL-0311 prompt/criteria and independent audit, accepted PL-0310/PL-0311 contracts, M13 final audit, M09 physical-validation deferral, ADR-0005, and current Label Zone/placement contracts.
- Starting synchronized SHA: `e9d4ce498b79952ffd1791877d7a937cb1ebbf81`; `git fetch origin main` confirmed local/origin equality and clean status before investigation.
- Execution worktree: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`. The dirty, 345-commit-behind Desktop owner checkout was preserved. Authorized push target: `origin/main`.
- PL-0312 V02 is builder-green and its indexes record PL-0313 as next. Accepted PL-0310/PL-0311 implementation/evidence is unchanged. M15+ was not started.

## Investigation and stop condition

- No product source or test file was changed. Work stopped before implementation because the accepted Label Zone contract does not define a conversion from its boundary to millimetres on the source CAD surface.
- `LabelZoneBoundary` is explicitly a normalized feature-local UV rectangle bounded by `[0,1]`; its serialized placement unit is `unitless_normalized`. The zone pins exact model/BREP/digest, parent, unit, component and feature provenance but carries no physical width/height or normalized-UV-to-surface-metric transform.
- `LabelZonePlacementRevision` preserves the same normalized domain and canonical orientation; it does not supply a BREP surface selector or metric extent. PL-0312 V02 region IDs are advisory, BREP-scoped analysis evidence and are not stable CAD face IDs or an accepted UV mapping.
- BREP numerical geometry alone cannot establish which surface parameterization, extents, seam, or unrolling rule the normalized Label Zone boundary uses. Treating `[0,1]` as millimetres, scaling by a whole-solid bounding box, or selecting a transient face/order would invent the required conversion. Wrap geometry has no accepted unroll rule either.
- PL-0313 requires a millimetre dieline from the accepted Label Zone and says RELATIVE sources fail closed. The R01 continuation stop rules prohibit proceeding through unresolved authority ambiguity. A source contract/owner decision must define the stable metric surface mapping and, for wrap, the flattening/seam policy before this can be implemented truthfully.
- A read-only source search found no existing Label Zone dieline or normalized-surface-to-millimetre mapping contract. No alternative transform was inferred.
- PL-0314 through PL-0331 were not started. No M15 work began.

## Validation and publication

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `git fetch origin main`; `git rev-list --left-right --count HEAD...origin/main`; `git status --short --branch` | Confirm synchronized, clean task starting point. | PASS: 0 ahead / 0 behind; clean at `e9d4ce498b79952ffd1791877d7a937cb1ebbf81`. |
| Read Label Zone and placement source contracts; search `core/src/packlab_core` and tests for dieline or label UV metric mapping | Identify an accepted exact mapping that can convert normalized zone extent to mm. | STOP: the accepted contracts provide only unitless normalized UV and canonical axes; no surface metric transform or wrap unroll/seam contract exists. |
| Focused/full tests, static and dependency checks | Run only after the required source mapping authority exists and implementation is in scope. | NOT RUN: authority stop preceded implementation; no validation PASS is claimed. |
| Privacy/scope/source mutation review | Confirm no PL-0313 product changes or future-task changes. | PASS: no source/test/dependency/tracker edits were made; only this blocker evidence is prepared. |
| Child log publication | Publish this blocker log separately and verify remote parity. | To be recorded in the separate log-only publication commit. |

## Exact blocker and required resolution

PL-0313 cannot derive millimetre dieline coordinates from an accepted Label Zone until an accepted contract binds its normalized feature-local UV boundary to exact metric CAD surface extents and defines wrap flattening/seam behavior. Numeric values may remain `mm_unverified`, but their conversion and geometry binding must be authoritative. No source geometry, UV, face identity, or mm scale was fabricated.

The R01 batch stops at PL-0313 before implementation. PL-0312 V02 remains `READY_FOR_INDEPENDENT_AUDIT`; PL-0313 has no implementation commit; PL-0314 through PL-0331 remain unstarted.

## Handoff

- No PL-0313 implementation/evidence commit exists because the authority stop preceded product edits.
- This blocker log is to be published in a separate log-only commit; the original M14 master log and R01 continuation log will record `BATCH_STOPPED` and end at `AWAITING_MILESTONE_AUDIT`.

READY_FOR_INDEPENDENT_AUDIT
