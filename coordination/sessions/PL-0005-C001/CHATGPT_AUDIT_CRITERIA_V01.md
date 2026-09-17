# PL-0005-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0005 — Create dependency/license register for NextLevel, COLMAP, OpenMVS, Open3D, OpenCV, PyTorch, OpenCascade bindings, Blender and PySide6.**

These criteria are frozen for Codex prompt V01.

## A. Safe synchronization and authorization

1. Codex proves the local workspace is `C:\Users\sekip\Desktop\PackLab`.
2. Codex verifies the Git root is the intended PackLab workspace.
3. Codex verifies `origin` resolves to `Sekiph82/PackLab`.
4. Codex runs `git fetch origin main --prune` before material implementation.
5. Codex records ahead/behind before any merge.
6. If local is only behind and tracked state is clean, synchronization uses `git merge --ff-only origin/main`.
7. Codex does not use reset, rebase, force-push, destructive checkout, silent stash, or `git clean`.
8. Local HEAD equals `origin/main` before material implementation.
9. Root `TASKS.md` authorizes PL-0005 for Codex before implementation.

## B. Required artifact and scope

10. `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` exists.
11. The register states it is governance/compliance documentation, not legal advice.
12. The register records an evidence/review date.
13. It states PL-0005 does not install, pin, vendor, bundle, link, modify, or distribute dependencies.
14. It states exact compatibility/version selection is later work.
15. The actual Codex range contains only the authorized register plus matching Codex log.
16. Root `TASKS.md` is not modified by Codex.
17. Existing architecture/governance/session artifacts are not modified by Codex.
18. No application/source/schema/runtime implementation is added.
19. No PL-0006+ work is implemented opportunistically.

## C. Register structure and provenance

20. Every required dependency/capability has a distinct register entry or clearly separated sub-entry.
21. Each entry records PackLab role.
22. Each entry records planned integration mode.
23. Each entry records current selection status.
24. Each entry records canonical upstream/source.
25. Each entry records primary license(s) without flattening known version/component distinctions.
26. Each entry includes authoritative license evidence URL(s).
27. Each entry records a third-party/transitive dependency caveat where relevant.
28. Each entry records a PackLab compliance/distribution note.
29. Each entry records version/pin status.
30. Each entry records follow-up task(s) where appropriate.
31. Each entry records risk/attention classification.
32. License claims prefer upstream LICENSE/COPYRIGHT/project documentation over mirrors/blogs/package aggregators.
33. The register does not copy large license texts unnecessarily; it records names, obligations/cautions at a factual summary level, and source links.
34. The register says license facts can vary by version/component/build configuration.
35. The register says transitive/optional dependencies actually shipped must be reviewed once versions/builds are pinned.

## D. NextLevel

36. NextLevel canonical upstream is `NextLevel/NextLevel`.
37. NextLevel primary license is recorded as MIT based on upstream LICENSE evidence.
38. NextLevel role is iOS camera-control abstraction behind PackLab-owned interfaces.
39. Exact NextLevel version remains unpinned and deferred to PL-0037 or later authorized work.
40. The register does not claim all future Swift package/transitive licensing is resolved merely because NextLevel itself is MIT.

## E. COLMAP

41. COLMAP itself is recorded under its official new BSD / 3-clause BSD terms.
42. COLMAP official license evidence is linked.
43. The official caveat that COLMAP third-party dependencies are separately licensed is recorded.
44. The register does not claim COLMAP's core BSD license automatically clears every binary build/distribution.
45. PackLab role is SfM/camera registration/sparse reconstruction behind an adapter.
46. Planned integration remains an external-engine boundary unless a later audited decision changes it.
47. Exact COLMAP version/build is unpinned in PL-0005.

## F. OpenMVS

48. Canonical upstream is `cdcseacave/openMVS`.
49. OpenMVS license is recorded as GNU AGPL v3 based on canonical evidence.
50. OpenMVS role is dense point cloud / mesh / refinement / texturing behind an external-engine boundary.
51. OpenMVS is classified **HIGH LICENSE ATTENTION**.
52. The register flags future distribution/bundling/modification/linking/service/network scenarios for explicit review.
53. The register does not declare a particular future PackLab closed-source/commercial distribution automatically compliant.
54. The register does not declare such distribution automatically impossible without analyzing the actual future integration/distribution model.
55. Explicit license review is required before PackLab distributes/bundles OpenMVS or materially changes its integration mode.
56. Exact OpenMVS version/build remains unpinned here.

## G. Open3D

57. Open3D canonical upstream/project evidence is linked.
58. Open3D primary license is recorded as MIT.
59. PackLab role is point-cloud/mesh analysis, cleanup, registration, measurement/deviation support.
60. The register still records third-party/build dependency review despite the permissive primary license.
61. Exact Open3D version remains unpinned.

## H. OpenCV

62. Official OpenCV license evidence is linked.
63. Register states OpenCV 4.5.0 and higher are Apache License 2.0 according to the official license page.
64. Register states OpenCV 4.4.0 and lower use 3-clause BSD according to the official license page.
65. Because PackLab has not pinned OpenCV, the register does not flatten all versions into one license.
66. PackLab role for OpenCV is recorded consistently with the architecture.
67. Final license/compliance record is tied to the later pinned version/build.

## I. PyTorch

68. Canonical PyTorch upstream license/packaging evidence is linked.
69. The main PyTorch project is recorded as BSD-3-Clause where supported by upstream evidence.
70. The register records that PyTorch source/package distributions include third-party components with separate licenses.
71. The register notes packaging metadata may represent multiple component licenses rather than one simplistic package-wide sentence.
72. The register does not claim the whole shipped PyTorch dependency graph is cleared by saying only “BSD”.
73. Later pinned package/build requires license/NOTICE/transitive review.
74. PackLab role is recorded consistently with analysis/segmentation/ML capability boundaries.

## J. Open CASCADE Technology (OCCT)

75. Canonical OCCT upstream is identified.
76. OCCT primary open-source license is recorded as LGPL 2.1 with the Open CASCADE special exception.
77. The OCCT exception evidence is referenced separately or clearly identified.
78. Alternative commercial licensing/contractual terms are recorded only as an upstream option, not selected by PL-0005.
79. PackLab role is engineering BREP/CAD/STEP capability.
80. OCCT licensing is kept separate from Python binding licensing.
81. Exact OCCT version remains unpinned here.

## K. Python OpenCascade binding layer

82. Final Python OpenCascade binding is explicitly `TBD / not selected`.
83. PL-0289 remains the binding selection/compatibility task.
84. The register explicitly says a Python binding may have a license different from OCCT itself.
85. The register does not assign OCCT's LGPL-2.1+exception to every possible Python binding.
86. If `pythonocc-core` is mentioned, it is identified only as a candidate, not a selected PackLab dependency.
87. If candidate license facts are stated, they have candidate-specific upstream evidence.
88. Risk/selection status visibly communicates that no binding is frozen by PL-0005.

## L. Blender

89. Blender official licensing page is referenced.
90. Blender software is recorded as GNU GPL, with the official page's GPL-version/distribution nuance represented accurately.
91. Blender role is external/headless UV/material/render/presentation automation, not dimensional truth.
92. The register distinguishes Blender software licensing from ordinary user-created artwork/render output ownership.
93. Distributed/published Blender Python scripts/add-ons are flagged for GPL-compatible licensing review based on Blender's own guidance.
94. The register does not state that rendered images/output automatically become GPL solely because Blender created them.
95. Exact Blender version remains unpinned.

## M. PySide6 / Qt for Python

96. Official Qt for Python licensing documentation is referenced.
97. PySide6/Qt for Python is recorded as available under LGPLv3/GPLv3 and Qt commercial licensing routes.
98. The register notes Qt modules/components/third-party contents can have additional or different licensing constraints.
99. PackLab role is Windows desktop presentation/UI.
100. Final packaging/distribution must review the actual Qt/PySide modules shipped and the selected licensing route.
101. The register does not declare proprietary distribution automatically cleared merely because LGPL is an option.
102. The register does not claim PackLab has purchased/selected a commercial Qt license.
103. Exact PySide6/Qt version remains unpinned here.

## N. Risk classification quality

104. LOW ATTENTION is defined as permissive primary licensing that still needs notices/transitive review.
105. MEDIUM ATTENTION is defined for version/build/module-sensitive obligations.
106. HIGH LICENSE ATTENTION is defined for strong-copyleft or architecture/distribution-sensitive dependencies requiring explicit review.
107. TBD / NOT SELECTED is defined for unfrozen component choices.
108. OpenMVS is HIGH LICENSE ATTENTION.
109. Python OpenCascade binding is TBD / NOT SELECTED.
110. OpenCV's version-sensitive status is visible.
111. PySide6/Qt is not mislabeled as unconditional permissive licensing.
112. Classification is explicitly governance triage, not a legal opinion.

## O. Architecture preservation

113. External engines remain behind PackLab-owned adapters/capability boundaries.
114. The register does not assert that CLI/external-process integration itself proves a legal conclusion.
115. Integration mode is recorded because it matters to later distribution/compliance review.
116. NextLevel remains behind PackLab-owned capture interfaces.
117. PySide6 UI does not become domain truth.
118. Blender does not become dimensional truth.
119. The register does not alter Scan Master / Design Model ownership rules.
120. The register does not introduce an ADR-worthy architecture change without an ADR.

## P. Distribution-scenario matrix

121. A scenario matrix exists.
122. Personal/local-only use is included.
123. Public source repository is included.
124. PackLab Windows installer/binary distribution is included.
125. Bundling third-party binaries is included.
126. Modifying third-party source is included.
127. Network/service deployment involving possible AGPL software is included.
128. Each scenario states what must be re-reviewed rather than offering unsupported legal certainty.
129. OpenMVS/AGPL is explicitly revisited in relevant distribution/network scenarios.
130. PySide6/Qt packaging obligations are revisited in binary distribution scenarios.
131. Actual shipped transitive dependencies/notices are revisited in binary/bundling scenarios.

## Q. Future-release compliance checklist

132. Checklist requires exact version/commit pinning.
133. Checklist requires saving license/NOTICE evidence for pinned versions.
134. Checklist requires inventorying transitive dependencies actually shipped.
135. Checklist records integration mode: linked/external executable/bundled/modified/downloaded separately as applicable.
136. Checklist requires preserving required copyright/license notices.
137. Checklist requires source/source-offer/source-availability review for copyleft components where applicable.
138. Checklist requires review of PySide6/Qt modules actually shipped.
139. Checklist requires review of distributed Blender scripts/add-ons.
140. Checklist requires explicit OpenMVS integration/distribution review.
141. Checklist requires separate review of the chosen OpenCascade Python binding.
142. Checklist states the register is not legal counsel.

## R. Validation and log contract

143. `git diff --check` is recorded passing.
144. New-file review uses `git add -N`, staged diff, or another command that actually displays the new file.
145. Explicit checks prove all required dependency entries exist.
146. Explicit checks verify authoritative evidence exists for every material license claim.
147. Explicit checks verify OpenMVS AGPL/high-attention handling.
148. Explicit checks verify COLMAP third-party caveat.
149. Explicit checks verify OpenCV version-sensitive licensing.
150. Explicit checks verify PyTorch third-party/package caveat.
151. Explicit checks verify OCCT/binding separation and binding TBD status.
152. Explicit checks verify Blender software/output distinction.
153. Explicit checks verify PySide6 multi-route/module-sensitive licensing.
154. Explicit checks verify no dependency is falsely claimed installed/pinned/distribution-cleared.
155. Explicit checks verify no legal-advice conclusion is presented as fact.
156. Explicit checks verify protected-file isolation and no PL-0006+ work.
157. Matching `CODEX_LOG_V01.md` exists.
158. Log points to prompt V01 and criteria V01.
159. Log records authoritative URLs consulted.
160. Log records synchronization, validation commands, expected results, failure conditions and actual results.
161. Log records ambiguity/conflicts in upstream evidence without guessing.
162. Log records implementation commit and push/remote visibility evidence.
163. Log does not predeclare the future log-containing SHA as `finalCommit` or equivalent.
164. Handoff is `AWAITING_AUDIT`; Codex does not self-assign PASS.
165. No secrets, credentials, signing material, private scans, supplier-confidential content or proprietary production artwork are committed.

## Audit evidence rule

License claims are time/version-sensitive. ChatGPT must independently inspect the actual GitHub register/diff and verify material contemporary claims against authoritative upstream sources rather than accepting Codex's summary. For strong-copyleft/multi-license dependencies, the audit must prefer a conservative factual description over a speculative legal conclusion.

## Closure rule

ChatGPT may mark PL-0005 complete only when all 165 mandatory criteria pass and no material licensing ambiguity is falsely resolved.

If any mandatory criterion fails:

- PL-0005 remains unchecked;
- ChatGPT writes `CHATGPT_AUDIT_V01.md` with exact findings;
- ChatGPT updates root `TASKS.md` to `CHANGES_REQUIRED`, `BLOCKED`, `OWNER_REQUIRED`, or another truthful state;
- ChatGPT issues `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md` when remediation is appropriate.
