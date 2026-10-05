# PL-0313 - Codex Prompt V02

Task: **Generate deterministic 2D label dielines in mm_unverified from explicit metric surface bindings**
Milestone: **M14 - Labels, Materials & Rendering**
Cycle: **M14-C001-R02**

This V02 supersedes PL-0313 V01 after the independently accepted authority stop.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_PARTIAL_AUDIT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the execution checkout non-destructively with latest `origin/main`. Preserve owner-local work. Verify live root `TASKS.md` authorizes M14-C001-R02 / PL-0313 V02.

Read before implementation:

- M14 partial audit V02;
- PL-0312 V02 prompt, criteria, implementation contract and independent audit;
- accepted PL-0310/PL-0311 contracts/audits;
- PL-0313 V01 blocker log;
- M13 final audit;
- M09 physical-validation deferral;
- ADR-0005.

Do not edit root `TASKS.md`.

## Frozen authority contract

The accepted Label Zone boundary remains normalized design intent. PL-0313 V02 must not reinterpret it as millimetres by itself.

Introduce an immutable, deterministic **Label Metric Surface Binding** that binds:

1. one exact Label Zone / Label Zone Placement revision;
2. exact Design Model revision;
3. exact CAD BREP revision and geometry digest;
4. one explicitly selected PL-0312 analysis-region candidate from that exact BREP;
5. one supported metric mapping mode;
6. exact mapping parameters and limitations.

The binding is derived design evidence. It does not modify or replace Design Model/CAD/Label Zone authority.

No persisted native face index, face traversal order, transient OCCT topology identity, preview triangle ID or mesh index may be used as the binding identity.

To resolve the exact host surface at runtime, implementation may recompute exact BREP analysis and match the selected PL-0312 `analysis_region_id` / canonical geometric evidence. Resolution must return exactly one compatible host surface or fail closed.

## Mandatory unit gate

Before creating a metric binding or dieline:

- `ScaleState.RELATIVE` / `reconstruction_units` => fail closed;
- only `ScaleState.METRIC_UNVERIFIED` / `mm_unverified` may proceed;
- every numerical metric output must remain labelled `mm_unverified`;
- no physical calibration/print-fit/manufacturing claim is permitted.

## Supported mapping mode A - PLANAR_RECTANGULAR

For FRONT/BACK zones:

- the selected analysis region must resolve uniquely to an exact planar trimmed CAD face on the pinned BREP;
- the exact trimmed host domain must be a single rectangle compatible with the accepted PackLab front/back label frame within explicit software tolerances;
- derive the planar local 2D basis from the accepted Label Zone surface frame, not arbitrary BREP parameter orientation;
- derive the metric host width/height from exact CAD geometry in `mm_unverified`;
- map normalized `u,v` linearly into the exact metric host rectangle;
- validate the mapped zone polygon against the exact trimmed host face;
- non-rectangular, multiply resolved, degenerate, incompatible or ambiguous planar surfaces fail closed.

Do not use a whole-solid bounding box as a substitute for the host surface rectangle.

## Supported mapping mode B - CYLINDRICAL_WRAP

For WRAP zones:

- the selected analysis region must resolve uniquely to an exact cylindrical CAD face on the pinned BREP;
- derive exact cylinder radius and axial extent from CAD geometry in `mm_unverified`;
- require cylinder axis/orientation compatibility with the accepted PackLab wrap surface-frame contract; otherwise fail closed;
- use the explicit accepted wrap seam direction from the Label Zone surface-frame contract;
- define normalized `u=0` at the accepted seam and progress in the accepted azimuthal direction;
- flatten with exact cylindrical arc length:
  - `x = radius * angle_from_seam`;
  - `y = axial_distance`;
- normalized U maps through the accepted angular host domain;
- normalized V maps through the exact axial host extent;
- full-wrap or trimmed-wrap domains are allowed only when their angular/axial limits are uniquely and deterministically resolved from exact CAD geometry and do not cross an unresolved seam;
- ambiguous seam, incompatible axis, non-cylindrical host, non-unique resolution or unsupported trimmed topology fails closed.

No generic freeform flattening is authorized.

## Dieline output contract

Produce an immutable deterministic 2D dieline revision containing at minimum:

- exact zone ID and placement revision ID;
- exact model/BREP/digest/parent authority;
- exact selected analysis revision + analysis_region_id;
- metric-surface-binding revision ID and mapping mode;
- source `scale_state=METRIC_UNVERIFIED`;
- `coordinate_unit=mm_unverified`;
- ordered 2D boundary vertices with explicit winding;
- numerical width/height/extents;
- explicit source-to-dieline mapping metadata;
- deterministic identity/digest;
- limitations:
  - physical accuracy validation deferred;
  - print fit not verified;
  - no bleed/safe margin yet;
  - no shrink/material/manufacturing compensation;
  - no mold/manufacturing/regulatory authorization.

The output is derived design geometry only.

## Required validation

Cover at minimum:

### Authority and unit gates
- RELATIVE source rejects metric binding/dieline;
- mm_unverified source succeeds only with explicit supported binding;
- stale/mismatched zone, placement, model, BREP, geometry digest or PL-0312 analysis revision/candidate rejects;
- source objects remain immutable.

### PLANAR_RECTANGULAR
- known rectangular planar face with exact expected width/height;
- FRONT and BACK orientations;
- normalized sub-rectangle maps to expected mm_unverified coordinates;
- winding/orientation deterministic;
- non-rectangular trimmed planar face rejects;
- ambiguous/multiple host-surface resolution rejects;
- whole-solid bbox cannot substitute for host surface mapping.

### CYLINDRICAL_WRAP
- known cylinder radius/height with expected circumference/arc-length mapping;
- WRAP normalized full width produces expected `2*pi*R` extent when full circumference is accepted;
- partial normalized wrap produces expected arc length;
- accepted seam direction/orientation is explicit and deterministic;
- incompatible cylinder axis, ambiguous seam, unsupported trim or non-cylinder rejects;
- no transient face/topology ID appears in persisted identity.

### Determinism/safety
- repeated exact inputs produce identical binding/dieline IDs and payloads;
- reordered/transient face traversal does not change output when exact geometry is unchanged;
- non-finite/degenerate tolerances or dimensions reject;
- no raster/pixel/tessellation source authority.

Run focused predecessor/regression tests, locked full repository suite, changed-file Ruff/format, targeted mypy/compile checks, dependency/lockfile check, privacy/security/scope review and remote publication verification.

## Handoff

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M14-C001/PL-0313_CODEX_LOG_V02.md`

in a separate log-only commit.

The V02 log must record:

- V01 blocker resolution;
- metric binding contract;
- exact supported/unsupported mapping modes;
- unit gates;
- source/test files;
- focused/full/static results;
- limitations;
- final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
