# PL-0404 — Physical inventory prioritization rubric

**Rubric proposal only. No real POVU SKU or physical Kenya inventory is currently ranked.**

## Gate before scoring

Only score a candidate after the PL-0403 record identifies an actual physical package/component and an authorized product/SKU owner provides a current launch/use matrix. Every scored field must cite its source, evidence date and confidence. Task ordering, mockups, synthetic fixtures and category examples do not establish commercial launch priority.

Do not score a candidate with unknown identity, unverified stock existence, unknown sample custody/safety or no owner-approved SKU/launch linkage. Mark `UNRANKED_INPUT_REQUIRED` and state which evidence is missing. Keep supplier names, customer identity, launch dates, volumes and confidential product data in access-controlled internal metadata.

## Proposed weighted score

Score each criterion from 0 to 5. The weights are a starting method for discussion, not an owner-approved launch strategy. Compute `weighted_total = sum(score / 5 × weight)` only when all six criterion scores are supported by evidence. If any score or required gate is unknown, emit no numeric total/band and set `UNRANKED_INPUT_REQUIRED`; never sum partial weights or impute missing scores.

| Criterion | Weight | Evidence expected |
| --- | ---: | --- |
| Confirmed launch relevance / owner priority | 30% | Dated internal product/launch record and authorized priority from owner/product lead |
| Reuse across distinct, active SKUs | 25% | Current SKU-to-asset matrix; count unique active SKU IDs, not artwork variants unless relevant |
| Readiness and dependency unlock | 15% | Verified prerequisites plus specific dependent workflow(s) enabled |
| Supply/sample readiness | 10% | Confirmed physical sample exists, can be accessed safely, and provenance/owner authority is adequate |
| Geometry-information benefit | 10% | Evidence-backed geometry/feature gap, dimensional/closure importance, family uniqueness and downstream use |
| Capture effort / station fit | 10% | Measured size/mass, PL-0396 fit, treatment restrictions and estimated session effort; high effort lowers score |

Suggested criterion-specific anchors below are a calibration proposal. A score must cite contemporaneous source records; disputed evidence is `UNRANKED_INPUT_REQUIRED` until resolved.

| Criterion | 0 | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Confirmed launch relevance (30%) | Owner/product source says not in scope | No confirmed launch link | Candidate link only, not in dated plan | Included in approved plan, timing distant/unspecified | Confirmed launch within planned cycle | Explicitly owner-designated critical or launch-blocking |
| Reuse across active SKUs (25%) | 0 active SKUs | 1 | 2 | 3–4 | 5–9 | 10+ distinct active SKU IDs |
| Readiness/dependency unlock (15%) | Verified, non-safety prerequisite means no delivery in the scoring horizon | Multiple significant non-safety prerequisites unresolved | One major non-safety prerequisite unresolved | Ready, no documented downstream blocker | Ready and unblocks one verified dependent task | Ready and unblocks multiple or owner-critical dependencies |
| Supply/sample readiness (10%) | Inventory exists but owner-confirmed access is only after the scoring horizon | Access/custody date is uncertain, with an authorized verification path | Sample accessible, but some noncritical provenance fields are unknown | Safe and authorized sample exists; core provenance fields recorded | Sample and custody/material evidence verified | Same, plus required interface/reference evidence available |
| Geometry-information benefit (10%) | No distinct geometry information needed | Low-priority already-covered geometry | Minor missing features | A unique family or feature gap is documented | Important closure/fit/dimension feature gap | Critical fit/geometry gap affects multiple verified SKUs/workflows |
| Capture effort / validated station fit (10%, reversed) | High documented effort within an otherwise safe/authorized feasible method | Major station extension required | Outside current verified envelope but feasible change identified | Near envelope limit or substantial extra setup | Fits with documented minor adjustments | Fits tested station with ordinary repeatable setup and low effort |

For the effort criterion, `5` means low verified effort and within a physically validated station envelope; `0` means high, documented effort within an otherwise safe/authorized feasible method. The table's weights sum to 100, so a fully evidenced total spans 0–100. An unverified size or mass is unknown, not a high-fit score. Unsafe, unauthorized, unknown-use or missing-inventory candidates are excluded by the gate and do not receive any numeric score.

Suggested queue bands after evidence is complete: `P1` ≥75, `P2` 55–74.99, `P3` <55. An unresolved owner-priority gate, unsafe/unknown sample, or any required evidence field missing overrides numeric score to `UNRANKED_INPUT_REQUIRED`; the formula cannot bypass safety, owner or physical prerequisites. Use a tie-break sequence of (1) higher confirmed owner launch priority, (2) more distinct active SKU reuse, (3) unlocks a blocked dependent workflow, then (4) lower safe capture effort. Record rubric version, scorer/date, sources and any tie decision.

## Reusable inventory-to-SKU matrix template (blank)

Use one row per package/component ↔ active SKU relationship. Repeat package ID across rows when reused. Use access-controlled identifiers/references; no names or production details should be copied into public artifacts.

| Package/component ID | Entity kind / physical existence evidence | Active SKU ID | SKU status / source date | Owner launch priority / source | Asset/artwork/geometry link | Evidence reference / reviewer |
| --- | --- | --- | --- | --- | --- | --- |
| __________________ | __________________ | __________________ | __________________ | __________________ | __________________ | __________________ |
| __________________ | __________________ | __________________ | __________________ | __________________ | __________________ | __________________ |
| `SYNTHETIC-TEST-PKG-0001` (synthetic only) | NOT REAL; existence `UNKNOWN` | `SYNTHETIC-TEST-SKU-0001` | NOT REAL / no source date | NONE / no launch source | synthetic example only | none; `UNRANKED_INPUT_REQUIRED` |

## Score summary template (blank)

| Field | Value / evidence reference |
| --- | --- |
| Canonical asset/component ID and PL-0402 ID status | __________________ |
| Physical existence, count, custody, condition (PL-0403 source) | __________________ |
| Verified distinct active SKU IDs / count / source date | __________________ |
| Owner-approved launch priority and source | __________________ |
| Dependency unlocks / source | __________________ |
| Sample safety, material/provenance confidence | __________________ |
| Station fit and capture effort evidence | __________________ |
| Scores: launch / reuse / readiness / supply / technical / effort | ___ / ___ / ___ / ___ / ___ / ___ |
| Weighted score / band / unknown override | __________________ |
| Reviewer, scoring date, rubric version, exceptions | __________________ |

## Synthetic example (not a ranking)

`SYNTHETIC-TEST-PKG-0001` has `UNKNOWN` inventory existence and no real SKU/launch source. Its value is `UNRANKED_INPUT_REQUIRED`; do not assign product priority or include it in a real queue. This shows missing-data handling only and is not a POVU SKU, physical package or Kenya inventory entry.

## Current blocker and handoff

The current repository context has no authorized physical inventory or active POVU launch/SKU matrix. Therefore this rubric does not rank any real bottle, jerrycan, jar, tube, sachet, closure, trigger or pump. PL-0403 remains externally blocked, and actual PL-0404 prioritization remains open until both evidence sources exist. No product order is inferred from the order of PL-0405–0409 tasks.

## Limits

This proposed scoring method has not been calibrated against actual launch outcomes or owner-approved strategic weights. It does not establish demand, supplier availability, actual sample reuse, manufacturing readiness, site safety or capture performance. Any future scoring must preserve the source record and may change with launch plans and inventory evidence.
