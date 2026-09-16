# PL-0002-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0002 — Create project glossary covering Scan Mesh, Design Model, Digital Twin, PackScan, Label Zone, BREP, SfM and MVS.**

These criteria are frozen for Codex prompt V01.

## A. Safe synchronization

1. Codex proves local workspace is `C:\Users\sekip\Desktop\PackLab`.
2. Codex verifies Git root and `origin` identity as `Sekiph82/PackLab`.
3. Codex runs `git fetch origin main --prune`.
4. Codex records ahead/behind before any merge.
5. Synchronization uses fast-forward-only when local is only behind.
6. Codex does not use reset/rebase/force-push/destructive checkout/silent stash.
7. Codex does not use `git clean` in this normal session.
8. Local HEAD equals `origin/main` before material implementation.
9. Root `TASKS.md` authorizes PL-0002 before implementation.

## B. Required artifact and scope

10. `docs/architecture/GLOSSARY.md` exists in the audited implementation.
11. `docs/architecture/REPOSITORY_STRUCTURE.md` remains unchanged by Codex.
12. No application/source/schema implementation is added.
13. No PL-0003+ work is implemented opportunistically.
14. Root `TASKS.md` is not edited by Codex.
15. ChatGPT prompt/criteria/audit artifacts are not edited by Codex.
16. Governance files and prior PL-0001 session evidence remain unchanged by Codex.

## C. Required terminology coverage

17. PackLab Capture is defined.
18. PackLab Studio is defined.
19. PackScan / `.packscan` is defined.
20. Source Evidence / Raw Capture is defined.
21. Reconstruction Intermediate is defined.
22. Scan Mesh is defined.
23. Scan Master is defined.
24. Design Model is defined.
25. Digital Twin is defined.
26. Parametric Geometry is defined.
27. Profile is defined.
28. Cross-Section is defined.
29. Feature / Parametric Feature is defined.
30. BREP / B-Rep is defined.
31. STEP is defined.
32. SfM is defined.
33. MVS is defined.
34. Camera Intrinsics is defined.
35. Camera Extrinsics / Pose is defined.
36. Calibration is defined.
37. Scale / Metric Scale is defined.
38. Coordinate System is defined.
39. Label Zone is defined.
40. Dieline is defined.
41. Artwork is defined.
42. Material Assignment / PBR Material is defined.
43. Packaging Asset is defined.
44. Component / Assembly is defined.
45. Provenance is defined.
46. Fixture / Public Test Fixture is defined.

## D. Architectural distinction quality

47. Definitions are PackLab-specific and not generic dictionary-only sentences.
48. Scan Mesh is explicitly not editable engineering/CAD truth.
49. Scan Master is explicitly a promoted/normalized reference distinct from raw reconstruction and Design Model.
50. Design Model is explicitly separate, editable and parameter-driven.
51. Design Model may derive from Scan Master without mutating the Scan Master.
52. Digital Twin is not reduced to a pretty mesh or single file.
53. Digital Twin distinguishes asset identity from representations/revisions and does not require every optional layer to exist.
54. PackScan is defined as versioned Capture-to-Studio interchange/container without prematurely freezing PL-0044+ schema details.
55. SfM and MVS are correctly distinguished conceptually.
56. COLMAP is identified as the planned PackLab SfM/sparse boundary and OpenMVS as the planned dense MVS boundary.
57. SfM/MVS output is not presented as engineering CAD truth or certified metric accuracy by itself.
58. BREP is distinguished from STEP.
59. STEP is treated as interchange/export rather than the conceptual source-of-truth Design Model.
60. Label Zone, Dieline and Artwork are clearly separated.
61. Artwork remains separate from engineering body geometry.
62. Material/PBR/rendered appearance is not allowed to redefine engineering dimensions.

## E. Ownership, mutability and dependency clarity

63. Material terms identify ownership/creator or lifecycle role where needed to avoid ambiguity.
64. Source/protected vs derived/regenerable vs editable vs presentation concepts remain consistent with `REPOSITORY_STRUCTURE.md`.
65. Provenance definition supports tracing derived assets back to source/settings/revisions where applicable.
66. Packaging Asset and Digital Twin definitions do not collapse asset identity into a single mesh/export file.
67. Component/Assembly definition supports reusable bottle/closure/trigger/pump relationships without implying geometry duplication.
68. Camera intrinsics/extrinsics, calibration, scale and coordinate-system definitions do not falsely promise certified metrology.

## F. Cross-reference and precedence

69. Glossary references `docs/architecture/REPOSITORY_STRUCTURE.md`.
70. Glossary states future normative schema details belong in `schemas/` contracts where applicable.
71. Glossary states it does not override root `TASKS.md`, active session scope, normative schemas or audited ADRs.
72. Glossary does not create a second tracker or workflow state surface.

## G. Validation and evidence

73. `git diff --check` is recorded as passing.
74. Explicit content checks cover all 30 required terms.
75. Explicit checks cover Scan Mesh / Scan Master / Design Model distinctions.
76. Explicit checks cover Digital Twin semantics.
77. Explicit checks cover PackScan scope restraint.
78. Explicit checks cover SfM/MVS and COLMAP/OpenMVS roles.
79. Explicit checks cover BREP/STEP distinction.
80. Explicit checks cover Label Zone/Dieline/Artwork separation.
81. Explicit checks cover material/rendering non-authority over dimensions.
82. Matching `CODEX_LOG_V01.md` exists.
83. Log corresponds to prompt V01 and criteria V01.
84. Log records exact commands/results, expected outcomes, explicit failure conditions and failures/fixes.
85. Log records implementation commit and push/remote visibility evidence.
86. Codex handoff is `AWAITING_AUDIT` and does not self-assign PASS.
87. Actual GitHub diff is limited to the authorized glossary and matching Codex log, excluding ChatGPT-owned lifecycle/session setup commits already present before Codex starts.
88. No secrets, credentials, signing material, private scans, supplier-confidential content or proprietary production artwork are committed.

## Audit evidence rule

Codex synchronization/test commands are E1/E2 until independently reproducible by ChatGPT. ChatGPT must inspect the actual GitHub diff and glossary content and explicitly disclose any command it cannot independently rerun.

A complete term count is not sufficient if definitions violate PackLab architecture or collapse distinct representations.

## Closure rule

ChatGPT may mark PL-0002 complete only if all mandatory criteria pass and no material ambiguity remains.

If any mandatory criterion fails:

- PL-0002 remains unchecked;
- ChatGPT writes `CHATGPT_AUDIT_V01.md` with exact findings;
- ChatGPT updates root `TASKS.md` to `CHANGES_REQUIRED` or other truthful state;
- ChatGPT issues `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md`.
