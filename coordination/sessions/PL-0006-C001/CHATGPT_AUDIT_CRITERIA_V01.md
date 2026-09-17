# PL-0006-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0006 — Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.**

These criteria are frozen for Codex prompt V01.

## A. Authorization and synchronization

1. Root `TASKS.md` shows PL-0006 as current task, status `READY`, actor `CODEX` before material work.
2. Git root is `C:\Users\sekip\Desktop\PackLab`.
3. `origin` resolves to `Sekiph82/PackLab`.
4. `git status --porcelain` is recorded before material work.
5. `git fetch origin main --prune` runs before material work.
6. Explicit ahead/behind is recorded with `git rev-list --left-right --count HEAD...origin/main` before merge.
7. Tracked local changes cause STOP.
8. Ahead/diverged local state causes STOP.
9. Behind-only state uses only `git merge --ff-only origin/main`.
10. No reset, rebase, force-push, destructive checkout, silent stash, or `git clean` is used.
11. Local HEAD equals `origin/main` before material work.
12. Ahead/behind equals `0 0` before material work.
13. Historical `.hiveai/` is not staged or committed.

## B. Required artifact and scope

14. `docs/architecture/VERSIONING_POLICY.md` exists.
15. Only `VERSIONING_POLICY.md` plus matching `CODEX_LOG_V01.md` are added by Codex.
16. Root `TASKS.md` is not modified by Codex.
17. `AGENTS.md`, `CLAUDE.md`, `IMPLEMENTATION_GUIDE.md` are not modified.
18. Prior session artifacts are not modified.
19. No app/source/schema/runtime implementation is added.
20. No release tag, GitHub release, workflow, manifest, app version file, schema file, package manifest, lockfile, or executable tooling is created.
21. PL-0007+ work is not implemented.
22. No ADR is created unless prompt-required STOP condition is triggered; opportunistic architecture change is absent.

## C. Version-domain model

23. Three independent domains are explicitly defined: StudioVersion, CaptureVersion, PackScanSchemaVersion.
24. Policy says the three domains are related but not numerically locked.
25. Studio uses SemVer-style MAJOR.MINOR.PATCH.
26. Capture uses SemVer-style MAJOR.MINOR.PATCH.
27. PackScan schema uses explicit MAJOR.MINOR.PATCH semantics.
28. Task IDs are explicitly not semantic versions.
29. Commit SHAs are provenance, not semantic versions.
30. The document does not falsely claim a production release already exists.

## D. Studio/Capture SemVer semantics

31. MAJOR is defined for incompatible public behavior/API/project/runtime contract changes.
32. MINOR is defined for backward-compatible feature/capability additions.
33. PATCH is defined for backward-compatible fixes with no intended public compatibility break.
34. Internal refactoring alone does not force MAJOR if public compatibility remains intact.
35. Prerelease identifiers are explicitly allowed.
36. Examples include alpha/beta/rc forms.
37. `0.y.z` is identified as development-stage.
38. `0.y.z` does not waive explicit PackLab compatibility requirements.
39. Studio bug-fix example maps to PATCH.
40. Backward-compatible Studio feature example maps to MINOR.
41. Incompatible Studio contract example maps to MAJOR.
42. Capture UI-only fix example maps to PATCH.
43. Backward-compatible Capture capability example maps to MINOR.
44. Incompatible persisted Capture behavior/API example maps to MAJOR.

## E. PackScan schema bump semantics

45. Schema MAJOR is defined for incompatible structural or semantic change.
46. Required-field removal or incompatible rename maps to MAJOR.
47. Unit semantic change maps to MAJOR.
48. Coordinate-system semantic change maps to MAJOR.
49. Checksum interpretation change that breaks older readers maps to MAJOR.
50. Schema MINOR is backward-compatible additive change.
51. Optional field/file addition maps to MINOR only when older readers can safely tolerate it under the contract.
52. Optional enum/value evolution is treated conservatively and cannot silently break older readers.
53. Schema PATCH is limited to compatibility-preserving corrections/clarifications.
54. PATCH cannot silently change required fields.
55. PATCH cannot silently change units.
56. PATCH cannot silently change coordinate conventions.
57. PATCH cannot silently change checksum semantics.
58. PATCH cannot silently change required file meaning.
59. Documentation-only clarification rule explains when PATCH versus no schema bump is appropriate.
60. Policy avoids claiming every textual schema edit requires a schema version bump.

## F. Compatibility matrix

61. Older Studio reading newer schema is covered.
62. Newer Studio reading older schema is covered.
63. Older Capture output consumed by newer Studio is covered.
64. Newer Capture output consumed by older Studio is covered.
65. Unsupported future schema MAJOR is covered.
66. Supported older schema MAJOR with migration path is covered.
67. Same MAJOR with higher MINOR is covered.
68. Same MAJOR/MINOR with higher PATCH is covered.
69. Compatibility behavior requires explicit version/capability checks rather than guessing.
70. Matrix does not imply universal forward compatibility.
71. Matrix does not imply universal backward compatibility.
72. Future MAJOR is rejected cleanly unless explicitly supported.

## G. Reader behavior contract

73. Reader rejects unsupported future MAJOR cleanly.
74. Same-MAJOR newer MINOR is accepted only when additive/optional compatibility rules are actually preserved.
75. PATCH differences are accepted only when declared semantics remain compatible.
76. Reader never silently reinterprets units.
77. Reader never silently reinterprets coordinate frames.
78. Reader never silently reinterprets checksum rules.
79. Reader never silently reinterprets photo orientation semantics.
80. Reader never silently reinterprets calibration meaning.
81. Reader never silently reinterprets required file semantics.
82. Unsupported/incomplete/future versions produce clear diagnostics.
83. Raw imported `.packscan` input remains immutable during compatibility/migration handling.

## H. Writer behavior contract

84. Writer emits exactly one explicit schema version.
85. Writer cannot emit fields/files requiring behavior beyond its declared schema version.
86. Deterministic output implementation is deferred to later PackScan tasks.
87. Writer rules do not create schema implementation in PL-0006.
88. Capture release compatibility declarations are policy only, not implemented here.

## I. Migration policy

89. Migrations are explicit and versioned.
90. Migration identifies source version.
91. Migration identifies target version.
92. Migration is non-destructive relative to original `.packscan` evidence.
93. Migration failure does not partially overwrite source input.
94. Downgrade is not assumed possible.
95. Lossy migration must be explicit.
96. Lossy migration must be user/audit visible.
97. Migration implementation is deferred to later tasks.
98. Policy does not imply in-place mutation of immutable source evidence.

## J. Application-to-schema compatibility declarations

99. Future Studio/Capture releases must declare application version.
100. Future releases declare schema read range.
101. Future releases declare schema write version(s).
102. Future releases declare migration support range.
103. Future releases declare known incompatibilities.
104. PL-0363/PL-0364 remain responsible for coordinated release numbering/manifest implementation.
105. No release manifest is created by PL-0006.

## K. Git/release relationship

106. Git tags/releases are explicitly later work.
107. One monorepo may contain different Studio/Capture/schema versions.
108. Commit SHA supplements provenance but does not replace semantic version.
109. Future artifacts must record exact semantic versions and commit provenance.
110. No tag/release is created in this task.
111. Version examples are clearly examples unless explicitly frozen by a later authorized release decision.

## L. Canonical examples

112. Policy includes a Studio version example.
113. Policy includes a Capture version example.
114. Policy includes a PackScan schema version example.
115. Examples are unambiguous and use MAJOR.MINOR.PATCH.
116. Policy avoids presenting examples as already shipped production versions.
117. Optional PackScan metadata example maps to MINOR.
118. Required field removal/rename example maps to MAJOR.
119. Unit/coordinate semantic change example maps to MAJOR.
120. Breaking checksum semantics example maps to MAJOR.

## M. Architecture boundary preservation

121. Original `.packscan` input immutability is preserved.
122. Millimetres remain canonical engineering units unless a future audited ADR changes that contract.
123. Coordinate-system semantics remain explicit.
124. Scan Mesh / Scan Master / Design Model separation is not altered.
125. Public-repository safety remains intact.
126. No release implementation is pulled forward.
127. Versioning policy does not make UI/rendering layers source of dimensional truth.
128. Versioning policy does not introduce a second project-status tracker.

## N. Version source-of-truth hierarchy

129. Serialized PackScan declares its own schema version.
130. Built Studio exposes its own app version.
131. Built Capture exposes its own app version.
132. Future release manifest records compatibility/provenance.
133. Git commit SHA supplements provenance.
134. Git SHA does not substitute for semantic versions.
135. H!veAI/TASKS state is not conflated with app/schema version truth.

## O. Validation and evidence

136. `git diff --check` is recorded passing.
137. New-file diff review actually shows `VERSIONING_POLICY.md` via `git add -N` or equivalent.
138. Explicit content checks cover all three version domains.
139. Explicit content checks cover Studio/Capture bump semantics.
140. Explicit content checks cover schema MAJOR/MINOR/PATCH semantics.
141. Explicit content checks cover all required compatibility cases.
142. Explicit content checks cover reader behavior constraints.
143. Explicit content checks cover writer behavior constraints.
144. Explicit content checks cover migration constraints.
145. Explicit content checks cover application-schema declarations.
146. Explicit content checks cover required examples.
147. Explicit content checks cover Git/release separation.
148. Scope validation proves no unauthorized tracked file changed before log addition.
149. Matching `CODEX_LOG_V01.md` exists.
150. Log references prompt V01 and criteria V01.
151. Log records starting commit and implementation commit.
152. Log records exact sync commands/results.
153. Log records files read and changed.
154. Log records validation expected results, failure conditions and actual results.
155. Log records failures/fixes instead of hiding them.
156. Log records push/remote visibility evidence.
157. Log does not predeclare future final log-containing SHA.
158. Handoff is `AWAITING_AUDIT` and Codex does not self-assign PASS.
159. No secrets, credentials, signing material, private scans, confidential supplier content, or proprietary production artwork are committed.
160. Actual GitHub Codex range contains only the two authorized additions unless a documented `ADR_REQUIRED` stop prevented implementation.

## Closure rule

All **160 mandatory criteria** must pass.

ChatGPT must independently inspect the actual GitHub diff and policy semantics. A Codex-authored string-search harness is supporting evidence only, not independent proof.

If any mandatory criterion fails:

- PL-0006 remains unchecked;
- ChatGPT writes `CHATGPT_AUDIT_V01.md` with exact findings;
- root `TASKS.md` is updated to audited truth;
- a versioned remediation prompt/criteria is issued if appropriate;
- PL-0007 is not started.
