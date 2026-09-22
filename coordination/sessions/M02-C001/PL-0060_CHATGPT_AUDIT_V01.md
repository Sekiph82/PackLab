# PL-0060 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CHATGPT_AUDIT_CRITERIA_V01.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CODEX_LOG_V01.md

Audited implementation commit: 082db347c3ba880913d86f1ea0bce96a34e0fb6b

## Independent result

The committed A4/A3 SVG sources themselves encode nominal A4/A3 dimensions, four 40 mm marker placements, reference distances, 100 mm ruler bars, print-at-100% warnings and no physical-accuracy claim.

## Blocking test finding

The frozen task required static geometry tests that verify the encoded page size, marker size and reference distances from the actual source geometry.

`test_calibration_mats.py` verifies only duplicated `data-*` metadata attributes. It does not verify:
- root SVG `width`, `height` or `viewBox`;
- actual marker rectangle/path footprint;
- marker-center coordinates and derived inter-marker distances;
- actual reference-bar rectangle/tick geometry.

Therefore the visual/print geometry can drift while the metadata remains unchanged and the regression still passes. The boundary test also changes the expected argument rather than mutating actual SVG geometry.

## Criterion disposition

1-10: PASS
11: **FAIL** — static tests do not verify actual encoded SVG geometry.
12: **FAIL** — current regression is not sensitivity-bearing against geometry/metadata divergence.
13-17: PASS
18: **FAIL** — the log overstates geometry protection.

Result: **15 / 18 PASS, 3 FAIL**

## Required remediation

Keep the current SVGs unless a real geometry defect is found, but strengthen the static tests to derive geometry from the actual SVG:
- verify root width/height/viewBox in millimetres;
- derive marker bounds/centres from marker geometry and prove 40 mm size plus declared X/Y centre distances;
- verify the actual reference-bar length is 100 mm;
- add mutation/helper fixtures showing a geometry change with unchanged `data-*` metadata fails.

Decision: **CHANGES_REQUIRED**
