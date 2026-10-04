# PL-0312 - Codex Prompt V02

Task: **Implement curvature/slope analysis to suggest label-safe regions without inventing feature ownership**
Milestone: **M14 - Labels, Materials & Rendering**
Cycle: **M14-C001-R01**

This V02 supersedes PL-0312 V01 after the independently accepted authority stop.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_PARTIAL_AUDIT_V01.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the execution checkout non-destructively with latest `origin/main`, preserve owner-local work, and verify live root `TASKS.md` authorizes M14-C001-R01 / PL-0312 V02.

Read before implementation:

- M13 final audit;
- M09 physical-validation deferral;
- ADR-0005;
- PL-0310 and PL-0311 accepted contracts/audits;
- PL-0312 V01 blocker log;
- `cad_feature_map.py` accepted M13 mapping contract.

Do not edit root `TASKS.md`.

## Frozen authority resolution

The accepted M13 mapper is authoritative and must not be weakened or rewritten merely to make PL-0312 pass.

For exact CAD surface analysis:

- exact Design Model, BREP geometry digest, parent authority, unit state and stable **component_id** are mandatory provenance;
- a suggested CAD surface region may be identified as a **derived analysis region**, not as a permanent CAD face/topology identity;
- do not use face traversal index, OCCT transient topology identity, preview triangle index, mesh index, or sampling order as semantic authority;
- when M13 feature mapping is `AMBIGUOUS` or `UNRESOLVED`, the candidate must carry that truth explicitly:
  - `feature_attribution_status` = `AMBIGUOUS` or `UNRESOLVED`;
  - `resolved_feature_id` = null;
  - record the relevant contributing semantic feature IDs/statuses as evidence;
- feature-level ownership may be populated only if an already-accepted source contract provides an exact stable selector sufficient for that specific region. Do not create such a selector inside PL-0312.
- Candidate identity must be derived deterministically from exact source revision/digest + component + analysis parameters + canonicalized geometric evidence. If geometric signatures collide or cannot be made unambiguous, fail closed rather than attaching a topology index.

PL-0312 suggestions are advisory design evidence only. They do not create/approve a Label Zone automatically and do not imply physical label fit, printability, mold suitability, manufacturing approval or physical accuracy.

## Required implementation

Implement bounded deterministic curvature/slope analysis on exact validated CAD/BREP surfaces using the accepted OCP/OCCT adapter boundary.

The analysis must:

1. validate exact Design Model/BREP/parent/unit provenance and a stable component reference;
2. sample exact CAD surface differential properties through approved CAD adapter helpers, not preview pixels/mesh triangles as source truth;
3. use explicit bounded sampling density/limits and finite threshold inputs;
4. calculate curvature/slope evidence sufficient to classify candidate surface patches as advisory label-safe / not-safe under explicit thresholds;
5. canonicalize and deterministically order candidate/evidence records independent of transient face traversal order;
6. retain component-level provenance and truthful feature-attribution status;
7. expose limitations for seams, trimmed surfaces, discontinuities and any unsupported surface classes;
8. preserve RELATIVE/reconstruction_units and mm_unverified without authority escalation;
9. never mutate Design Model/BREP/Label Zone source authority.

A candidate may reference a derived `analysis_region_id` whose identity is valid only for the exact pinned source BREP digest and analysis contract. It must not be described as a stable CAD face ID.

## Required validation

Cover at minimum:

- planar box face / low-curvature candidate;
- cylindrical surface with expected curvature behavior;
- sloped planar surface / slope threshold boundary;
- highly curved or unsafe surface rejection/classification;
- the exact accepted revolve fixture where profile and axis are both ambiguous contributors to one solid:
  - analysis succeeds at component/whole-BREP level;
  - no feature is falsely selected;
  - feature attribution is explicitly AMBIGUOUS and `resolved_feature_id` is null;
- deterministic output and ordering under changed/transient face traversal order where testable;
- collision/fail-closed behavior for non-unique derived geometric signatures;
- bounded sampling and invalid/non-finite threshold rejection;
- captured and standalone parent propagation;
- RELATIVE and mm_unverified preservation;
- source immutability;
- no pixel/mesh-index/native-face-index authority.

Run focused predecessor/regression tests, the locked full repository suite, changed-file Ruff/format, targeted mypy/compile checks, dependency/lockfile check, privacy/security/scope review, and remote publication verification.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M14-C001/PL-0312_CODEX_LOG_V02.md` in a separate log-only commit.

The V02 log must record the V01 blocker resolution, exact feature-attribution behavior, source/test files, commands/results, limitations and final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
