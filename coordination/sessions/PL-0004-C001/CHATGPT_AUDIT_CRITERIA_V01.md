# PL-0004-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0004 — Document supported host/device baseline: Windows Acer laptop + iPhone 16 Standard, no LiDAR assumption.**

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
9. Root `TASKS.md` authorizes PL-0004 for Codex before implementation.

## B. Required artifact and scope

10. `docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md` exists.
11. The document is explicitly an architecture/support baseline, not production minimum-system-requirements certification.
12. The actual Codex implementation range contains only the authorized baseline document plus matching Codex log.
13. Root `TASKS.md` is not modified by Codex.
14. `AGENTS.md`, `CLAUDE.md`, `IMPLEMENTATION_GUIDE.md`, repository structure, glossary and ADR artifacts are not modified by Codex.
15. Coordination policy/index and prior session artifacts are not modified by Codex.
16. No application/source/schema/runtime implementation is added.
17. No PL-0005+ work is implemented opportunistically.

## C. Current Windows host evidence

18. Codex uses read-only local Windows queries to obtain current host facts.
19. Manufacturer is recorded from machine evidence, not guessed.
20. Model is recorded from machine evidence, not guessed.
21. If manufacturer materially conflicts with Acer, Codex stops rather than falsifying the task.
22. Windows edition/caption is recorded when available.
23. Windows version is recorded when available.
24. Windows build number is recorded when available.
25. OS architecture is recorded when available.
26. CPU model is recorded.
27. CPU physical-core count is recorded when available.
28. CPU logical-processor count is recorded when available.
29. Total physical RAM is recorded in a human-readable unit.
30. GPU name(s) are recorded.
31. Reported GPU adapter memory is either recorded with an appropriate reliability caveat or explicitly marked unknown/unreliable.
32. GPU driver version is recorded when available.
33. Canonical local PackLab workspace is `C:\Users\sekip\Desktop\PackLab`.
34. Observed host specifications are clearly described as the current primary owner machine, not universal PackLab minimums.

## D. Windows privacy / public-repository safety

35. No machine serial number is committed.
36. No BIOS serial is committed.
37. No hardware UUID is committed.
38. No Windows product key is committed.
39. No username/account identifier is committed.
40. No computer/device hostname is committed.
41. No MAC address is committed.
42. No IP address is committed.
43. No Wi-Fi SSID is committed.
44. No token, password, signing material or credential is committed.
45. Missing hardware facts are marked unknown/not verified rather than invented.

## E. Windows architectural role

46. PackLab Studio is documented as Windows-first for the owner workflow.
47. Python/PySide6 is assigned to the Windows Studio side.
48. COLMAP is documented as a Windows/Studio-side capability in the current architecture.
49. OpenMVS is documented as a Windows/Studio-side capability.
50. Open3D is documented as a Windows/Studio-side capability.
51. OpenCascade binding/CAD is documented as a Windows/Studio-side capability.
52. PyTorch/OpenCV are documented as Windows/Studio-side capabilities where applicable.
53. Blender is documented as a Windows/Studio-side rendering capability.
54. The baseline does not claim these external engines are already installed or working merely because they are architectural targets.
55. Exact dependency/version compatibility is explicitly deferred to PL-0005, PL-0027 and later engine tasks.

## F. iPhone 16 Standard baseline

56. The document says **iPhone 16 Standard**, not Pro or Pro Max, is the current capture baseline.
57. Owner-declared current capture-device status is distinguished from official external specification evidence.
58. Apple iPhone 16 technical-specifications source is referenced.
59. Apple ARKit runtime-support/configuration guidance is referenced.
60. A18 is recorded only as an official device fact relevant to the baseline.
61. 48 MP Fusion Main camera is recorded accurately.
62. 12 MP Ultra Wide camera is recorded accurately.
63. HEIF/JPEG still formats are recorded accurately if mentioned.
64. USB-C is recorded accurately if mentioned.
65. The document does not infer unsupported Pro-only hardware from the iPhone 16 Standard.
66. ARKit configuration support is treated as something code should runtime-check rather than blindly assume.

## G. Non-LiDAR architecture constraint

67. The document explicitly says PackLab Capture does not require LiDAR.
68. Standard iPhone 16 is the reason the architecture is designed without a LiDAR dependency, not an error state.
69. Core capture/reconstruction is image-based photogrammetry.
70. ARKit pose/world tracking is supporting metadata/guidance, not final geometry truth.
71. CoreMotion is supporting metadata/guidance, not final geometry truth.
72. Dense reconstruction remains on the Windows COLMAP/OpenMVS pipeline.
73. No core workflow depends on LiDAR-only depth/range APIs.
74. No core workflow depends on LiDAR-only scene-reconstruction/mesh APIs.
75. Optional future LiDAR support is classified as optional/future and would require later audited scope/ADR if it changes architecture.
76. Optional future LiDAR support does not silently remove the non-LiDAR path.
77. The baseline makes no claim that ARKit alone yields certified photogrammetric geometry.
78. The baseline makes no certified dimensional-accuracy claim.

## H. Capture policy boundary

79. Controlled high-resolution still photographs are identified as intended accepted reconstruction inputs.
80. Preview/video frames may be used later for live quality analysis/auto-trigger logic.
81. Final lens selection remains a later iOS task.
82. Final capture resolution/mode remains a later iOS task.
83. Focus/exposure/white-balance policy remains a later iOS task.
84. NextLevel/AVFoundation implementation details remain later iOS tasks.
85. PL-0004 does not freeze 48 MP capture as mandatory.
86. PL-0004 does not freeze RAW as mandatory.
87. PL-0004 does not freeze an exact photo count.
88. PL-0004 does not freeze a reconstruction-accuracy target.

## I. CI / macOS boundary

89. The document records GitHub Actions Windows for PackLab Studio build/test/package.
90. The document records GitHub Actions macOS for PackLab Capture Swift/iOS build/test/archive.
91. It states the owner does not need to own a Mac for the selected CI architecture.
92. It does not claim Windows is a native Xcode build host.
93. Native iOS builds are associated with an Apple/Xcode/macOS environment.
94. Simulator build and device signing are treated as separate concerns.
95. Signing/provisioning implementation is explicitly deferred to PL-0357+ / distribution tasks.

## J. Capability classification

96. A support/capability classification table exists.
97. REQUIRED BASELINE is defined or clearly used.
98. SUPPORTED PRIMARY PATH is defined or clearly used.
99. OPTIONAL / FUTURE is defined or clearly used.
100. NOT ASSUMED is defined or clearly used.
101. Windows host is classified.
102. iPhone 16 Standard is classified.
103. LiDAR is classified as not required / not assumed for the core path.
104. Discrete NVIDIA/CUDA acceleration is not made mandatory.
105. User-owned Mac hardware is not made mandatory.
106. Permanent internet/cloud connectivity during local reconstruction is not made mandatory.
107. GitHub Actions Windows/macOS are classified consistently with the selected CI architecture.

## K. Claims, limitations and future validation

108. The baseline explicitly says it is not a universal minimum-system-requirements specification.
109. Current observed host hardware is not presented as a performance guarantee.
110. External-engine compatibility remains to be validated later.
111. Physical camera/capture behavior remains to be validated later.
112. Reconstruction quality remains to be validated later.
113. Measurement accuracy remains to be validated later.
114. No mold-manufacturing/metrology certification is implied.

## L. Validation, evidence and log contract

115. `git diff --check` is recorded passing.
116. New-file review uses `git add -N`, staged diff, or another command that can actually display the new file.
117. Explicit checks cover prohibited sensitive identifiers.
118. Explicit checks cover iPhone 16 Standard identity and non-LiDAR requirement.
119. Explicit checks cover Windows/macOS CI role separation.
120. Explicit checks cover CUDA/Mac/internet non-requirements.
121. Explicit checks cover no future-task implementation and protected-file isolation.
122. Matching `CODEX_LOG_V01.md` exists.
123. Log points to prompt V01 and criteria V01.
124. Log records synchronization, host-fact commands/results, validation commands, expected results, failure conditions and actual results.
125. Log records implementation commit and push/remote visibility evidence.
126. Log does not predeclare the future log-containing commit SHA as `finalCommit` or equivalent self-referential metadata.
127. Handoff is `AWAITING_AUDIT`; Codex does not self-assign PASS.
128. No secrets, credentials, signing material, private scans, supplier-confidential content or proprietary production artwork are committed.

## Audit evidence rule

Codex-run local Windows hardware queries and local Git/PowerShell commands are E1/E2 until independently reproducible by ChatGPT. ChatGPT must independently audit the actual GitHub files, commit range, privacy exposure, device/CI semantics, architecture consistency and scope isolation.

For contemporary Apple device facts, ChatGPT should prefer official Apple sources. The task must not turn absence of LiDAR into a false claim that ARKit is unavailable; PackLab specifically uses ARKit as supporting non-LiDAR tracking metadata.

## Closure rule

ChatGPT may mark PL-0004 complete only when all 128 mandatory criteria pass and no material ambiguity remains.

If any mandatory criterion fails:

- PL-0004 remains unchecked;
- ChatGPT writes `CHATGPT_AUDIT_V01.md` with exact findings;
- ChatGPT updates root `TASKS.md` to `CHANGES_REQUIRED`, `BLOCKED`, `OWNER_REQUIRED`, or another truthful state;
- ChatGPT issues `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md` when remediation is appropriate.
