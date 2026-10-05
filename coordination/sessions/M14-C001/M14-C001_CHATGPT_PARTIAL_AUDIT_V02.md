# M14-C001 - ChatGPT Partial Milestone Audit V02

Date: 2026-10-05
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Independently accepted frontier: **PL-0310 through PL-0312**
Current blocked child: **PL-0313 V01**
Later children: **PL-0314 through PL-0331 not started**

## Accepted children

- PL-0310: `AUDITED_PASS`
- PL-0311: `AUDITED_PASS`
- PL-0312 V02: `AUDITED_PASS`

PL-0312 V02 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CHATGPT_AUDIT_V02.md

PL-0312 correctly preserves component/whole-BREP provenance, exact source/digest authority, BREP-scoped derived analysis regions and explicit ambiguous/unresolved feature attribution without inventing native face identity.

## PL-0313 V01 blocker

The builder stop is **VALID**.

The accepted Label Zone/placement contracts define the zone boundary in a unitless normalized [0,1] design domain. They do not define:

- a stable exact CAD host-surface binding for that normalized domain;
- metric width/height of the normalized host domain;
- a normalized-coordinate-to-mm transform;
- a stable planar surface chart;
- cylindrical wrap radius/axis/seam/unroll semantics;
- behavior for unsupported/non-developable freeform surfaces.

PL-0312 V02 analysis-region IDs are exact-BREP-scoped advisory evidence, not persistent CAD face IDs and not a metric UV chart. Therefore using a whole-solid bounding box, transient face order/identity, arbitrary BREP UV parameter extents, or treating [0,1] as millimetres would invent the missing mapping.

No PL-0313 product source/test changes were made. PL-0314 through PL-0331 were not started.

## Frozen authority resolution for PL-0313 V02

PL-0313 V02 may introduce an explicit **Label Metric Surface Binding** between:

- an accepted Label Zone/placement revision;
- the exact Design Model/BREP revision and geometry digest;
- one explicitly selected, accepted PL-0312 analysis-region candidate from that exact BREP;
- one supported metric mapping mode.

The binding is derived design evidence, not new physical authority.

### Supported mapping modes

**A. PLANAR_RECTANGULAR**

For FRONT/BACK zones:

- selected host surface must resolve uniquely to an exact planar trimmed CAD face from the pinned BREP by recomputing/matching accepted geometric evidence; no persisted native face index is allowed;
- the trimmed face must form a single rectangular metric domain compatible with the accepted PackLab label frame, within explicit software tolerances;
- metric width/height come from exact CAD geometry in `mm_unverified`;
- normalized zone coordinates map linearly into that exact rectangular domain;
- resulting zone polygon must be validated against the exact trimmed face;
- non-rectangular, ambiguous, multiply-resolved or incompatible planar domains fail closed.

**B. CYLINDRICAL_WRAP**

For WRAP zones:

- selected host surface must resolve uniquely to an exact cylindrical CAD face on the pinned BREP;
- the cylinder radius and axial extent come from exact CAD geometry in `mm_unverified`;
- the cylinder axis must be compatible with the accepted PackLab wrap frame, otherwise fail closed;
- the seam is the explicit accepted wrap seam direction from the Label Zone surface-frame contract;
- normalized U maps to exact arc length from that seam; normalized V maps to exact axial distance;
- full-wrap flattening uses `x = radius * angle`, `y = axial_distance` under the accepted orientation;
- incomplete/ambiguous cylindrical domains, incompatible axes or unresolved seam geometry fail closed.

Unsupported/freeform/non-developable mappings remain unsupported and fail closed. PL-0313 V02 must not invent a generic flattening algorithm.

### Unit and authority rule

- `ScaleState.RELATIVE` / `reconstruction_units` must fail closed before any mm dieline is emitted.
- Only `METRIC_UNVERIFIED` / `mm_unverified` sources can produce numerical-mm dielines.
- Output units remain explicitly `mm_unverified`.
- No output implies physical calibration, print-fit, shrink compensation, manufacturing, mold or regulatory approval.

## Resume rule

Execute:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CODEX_PROMPT_V02.md

against:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_CRITERIA_V02.md

If PL-0313 V02 closes green, continue PL-0314 through PL-0331 under the R02 continuation master. PL-0324 remains the real Blender capability gate.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

M14 remains open. Accepted frontier is PL-0312. Resume at PL-0313 V02. M15 remains unauthorized.
