# PL-0006-C002 - ChatGPT Strict Audit Criteria V01

Task: **PL-0006 - semantic versioning policy current-state re-entry**

Repository: https://github.com/Sekiph82/PackLab

Work order:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CODEX_PROMPT_V01.md

These criteria are frozen for C002/V01. All **100 mandatory criteria** must pass for `AUDITED_PASS`.

## A. Authority and current-state authorization

1. GitHub `main` is treated as repository truth.
2. Root tracker used for authorization is https://github.com/Sekiph82/PackLab/blob/main/TASKS.md.
3. Root `TASKS.md` shows PL-0006 as Current Task before material work.
4. Root `TASKS.md` shows PL-0006 status `CHANGES_REQUIRED` before material work.
5. Root `TASKS.md` shows Required Actor `CODEX` before material work.
6. Root `TASKS.md` points to PL-0006-C002 as the current work order.
7. Codex does not infer authorization from the first unchecked checkbox.
8. C001/V02 is treated as historical and unexecuted, not as completed evidence.
9. PL-0007 is not started.
10. Codex does not edit root `TASKS.md`.

## B. Exact synchronization before material validation

11. Git root is verified as the PackLab checkout.
12. `origin` is verified as https://github.com/Sekiph82/PackLab.git.
13. `git status --porcelain` is recorded before material validation.
14. `git fetch origin main --prune` runs before material validation.
15. `git rev-list --left-right --count HEAD...origin/main` is recorded before any merge.
16. Tracked local changes cause STOP.
17. Ahead-only local state causes STOP.
18. Diverged local state causes STOP.
19. Behind-only state uses only `git merge --ff-only origin/main`.
20. No reset, rebase, force-push, destructive checkout, silent stash, or `git clean` is used.
21. Historical local `.hiveai/` is not staged or committed.
22. Before material validation, local HEAD equals `origin/main`.
23. Before material validation, ahead/behind equals `0 0`.
24. Final pre-validation status contains no tracked local changes.
25. Exact synchronization commands and raw results are recorded in the C002 log.

## C. Existing policy preservation and scope

26. https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md exists.
27. The policy is not rewritten merely to manufacture a C002 implementation diff.
28. If unchanged, Codex proves it is unchanged against the synchronized C002 base.
29. If changed, the C002 log identifies a genuine substantive defect before the change.
30. Any policy correction is minimal and directly tied to that documented defect.
31. No application source is created or modified.
32. No PackScan schema implementation file is created or modified.
33. No release manifest is created.
34. No app version file is created.
35. No package manifest or lockfile is created.
36. No CI workflow is created.
37. No Git tag or GitHub release is created.
38. No dependency is installed or pinned.
39. No prior prompt, criteria, log, or audit artifact is modified.
40. If no substantive policy defect exists, the only C002 tracked addition is `coordination/sessions/PL-0006-C002/CODEX_LOG_V01.md`.

## D. Version-domain model

41. `StudioVersion` remains explicitly defined.
42. `CaptureVersion` remains explicitly defined.
43. `PackScanSchemaVersion` remains explicitly defined.
44. The three domains remain related but not numerically locked.
45. Studio remains SemVer-style MAJOR.MINOR/PATCH.
46. Capture remains SemVer-style MAJOR.MINOR/PATCH.
47. PackScan schema retains explicit MAJOR/MINOR/PATCH semantics.
48. Task IDs remain work identifiers, not semantic versions.
49. Commit SHAs remain provenance, not semantic versions.
50. The policy does not falsely claim a production release already shipped.

## E. Studio and Capture SemVer semantics

51. MAJOR remains for incompatible public behavior/API/project/runtime contract changes.
52. MINOR remains for backward-compatible feature/capability additions.
53. PATCH remains for backward-compatible fixes without intended public compatibility break.
54. Internal refactoring alone does not force MAJOR when public compatibility is preserved.
55. Prerelease identifiers remain allowed.
56. Alpha, beta, and release-candidate examples remain represented.
57. `0.y.z` remains identified as development-stage.
58. `0.y.z` does not waive PackLab compatibility requirements.
59. Studio bump examples remain internally consistent with the rules.
60. Capture bump examples remain internally consistent with the rules.

## F. PackScan schema semantics

61. Schema MAJOR remains required for incompatible structural or semantic change.
62. Required-field removal or incompatible rename remains MAJOR.
63. Unit semantic change remains MAJOR.
64. Coordinate-system semantic change remains MAJOR.
65. Breaking checksum interpretation remains MAJOR.
66. Schema MINOR remains limited to backward-compatible additive change.
67. Optional fields/files qualify for MINOR only when older readers can safely tolerate them.
68. Optional enum/value evolution remains conservative.
69. Schema PATCH remains compatibility-preserving.
70. PATCH cannot silently change required fields.
71. PATCH cannot silently change units.
72. PATCH cannot silently change coordinate conventions.
73. PATCH cannot silently change checksum semantics.
74. PATCH cannot silently change photo orientation or calibration meaning.
75. PATCH cannot silently change required file meaning.
76. Documentation-only clarification rules still distinguish PATCH from no schema bump.

## G. Compatibility matrix and behavior contracts

77. Older Studio reading newer schema is explicitly covered.
78. Newer Studio reading older schema is explicitly covered.
79. Older Capture output consumed by newer Studio is explicitly covered.
80. Newer Capture output consumed by older Studio is explicitly covered.
81. Unsupported future schema MAJOR is explicitly covered.
82. Supported older schema MAJOR with migration path is explicitly covered.
83. Same MAJOR with higher MINOR is explicitly covered.
84. Same MAJOR/MINOR with higher PATCH is explicitly covered.
85. Compatibility requires explicit version/capability checks rather than guessing.
86. The policy does not promise universal forward compatibility.
87. The policy does not promise universal backward compatibility.
88. Reader behavior rejects unsupported future MAJOR cleanly.
89. Reader behavior forbids silent reinterpretation of units, coordinate frames, checksums, orientation, calibration, and required file semantics.
90. Writer behavior emits one explicit schema version and cannot exceed its declared schema behavior.

## H. Migration, architecture, safety, and ownership

91. Migrations remain explicit, versioned, source/target bound, and non-destructive.
92. Migration failure cannot partially overwrite original source evidence.
93. Downgrade remains explicitly not assumed possible.
94. Lossy migration remains explicit and user/audit visible.
95. Future releases still declare app version, schema read range, schema write version(s), migration range, and known incompatibilities.
96. PL-0363/PL-0364 retain ownership of coordinated release numbering/release-manifest implementation.
97. Original `.packscan` evidence remains immutable and millimetres remain canonical engineering units unless a future audited ADR changes that contract.
98. Scan Mesh, Scan Master, and Design Model separation remains intact, and no UI/rendering layer becomes dimensional truth.
99. No secret, credential, signing material, private Kenya scan, confidential supplier data, or proprietary production artwork is committed.
100. The C002 log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/PL-0006-C002/CODEX_LOG_V01.md, records the required validation/scope/push evidence, does not self-assign an audit verdict, and ends with `AWAITING_AUDIT`.

## Closure rule

All 100 criteria are mandatory.

ChatGPT must independently inspect:

- the actual GitHub commit range;
- the actual changed files;
- the current `VERSIONING_POLICY.md`;
- the C002 log;
- the frozen C002 work order;
- root `TASKS.md`;
- architecture, privacy, scope, and regression boundaries.

Codex-run shell commands remain implementer evidence. ChatGPT must not treat them as independent runtime proof.

If all 100 criteria pass and no material defect is found, ChatGPT may write `CHATGPT_AUDIT_V01.md`, mark PL-0006 `[x]`, and advance the canonical tracker to PL-0007.

If any mandatory criterion fails, PL-0006 remains unchecked and ChatGPT must record the exact failure and issue the next remediation version or cycle.
