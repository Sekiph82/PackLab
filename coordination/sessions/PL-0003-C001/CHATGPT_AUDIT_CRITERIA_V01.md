# PL-0003-C001 — ChatGPT Strict Audit Criteria V01

Task: **PL-0003 — Create Architecture Decision Record (ADR) process and first ADR for the monorepo.**

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
9. Root `TASKS.md` authorizes PL-0003 for Codex before implementation.

## B. Required ADR-process artifact

10. `docs/architecture/adr/README.md` exists in the audited implementation.
11. README explains the purpose of ADRs in PackLab rather than being only a file-naming note.
12. README defines when a durable architectural choice requires an ADR.
13. Repository/module-boundary changes are identified as ADR-worthy.
14. Cross-platform contract/ownership changes are identified as ADR-worthy.
15. Major framework/runtime/tool selections are identified as ADR-worthy.
16. External-engine responsibility-boundary changes are identified as ADR-worthy.
17. Persistence/storage, geometry/CAD source-of-truth, security/trust, and CI/build/distribution architecture changes are covered as ADR-worthy categories.
18. README distinguishes ADR-worthy architecture decisions from routine implementation details, typo fixes, ordinary contract-preserving refactors, and task-status updates.

## C. ADR identity and lifecycle

19. ADR filenames use permanent sequential numeric IDs with lowercase kebab-case slugs.
20. The documented pattern is equivalent to `ADR-0001-<slug>.md`.
21. ADR numbers are never reused after rejection, deprecation, or supersession.
22. `Proposed` status is defined.
23. `Accepted` status is defined.
24. `Rejected` status is defined.
25. `Deprecated` status is defined.
26. `Superseded` status is defined.
27. Codex is not granted authority to self-accept an ADR.
28. ADR acceptance is tied to the audited PackLab task/session process and any required owner decision.
29. Accepted ADR history is preserved rather than rewritten to hide past decisions.
30. Material changes to an accepted ADR normally require a new ADR that supersedes the old one.
31. Non-semantic typo/link/format corrections may be made only without changing the decision and with traceable review.

## D. Required ADR structure

32. ADR ID and title are required.
33. Status is required.
34. Date is required.
35. Decision scope is required.
36. Context/problem is required.
37. Decision is required.
38. Rationale is required.
39. Alternatives considered are required.
40. Consequences/trade-offs are required.
41. Constraints/invariants are required.
42. Supersedes/Superseded-by metadata is required.
43. References/evidence are required.
44. README provides enough structural guidance/template material that a later ADR can be authored consistently without inventing a new format.

## E. Authority, precedence and ADR index

45. README states root `TASKS.md` remains the only live H!veAI/project-status tracker.
46. ADRs are explicitly architectural decision records, not progress/status trackers.
47. README references the role of `REPOSITORY_STRUCTURE.md`.
48. README references the role of `GLOSSARY.md`.
49. README states an ADR cannot silently override higher-authority active task/session scope.
50. README states that an accepted ADR intentionally changing a canonical architecture contract requires reconciliation of affected canonical documents in the same audited change or an explicitly authorized follow-up task.
51. Session prompts/logs/audits are treated as decision evidence, not ADR replacements.
52. README contains an ADR index table.
53. The index includes ADR ID, title and status.
54. The index supports a supersession relation or equivalent field.
55. The index contains ADR-0001 with status `Accepted`.

## F. First ADR identity and status

56. `docs/architecture/adr/ADR-0001-monorepo-architecture.md` exists.
57. ADR-0001 uses ID `ADR-0001` and an appropriate monorepo title.
58. ADR-0001 status is `Accepted`.
59. ADR-0001 contains a date.
60. ADR-0001 records that it formalizes the architecture already established by PL-0001 rather than claiming to invent an unrelated design.
61. ADR-0001 references the audited PL-0001 architecture evidence.
62. ADR-0001 references the audited PL-0002 glossary evidence.

## G. First ADR context and decision

63. ADR-0001 context identifies PackLab Capture as the iOS/iPhone product.
64. ADR-0001 context identifies PackLab Studio as the Windows product.
65. ADR-0001 context identifies the need for shared cross-platform contracts/documentation/test/tooling/coordination evidence.
66. ADR-0001 records a single PackLab monorepo as the decision.
67. ADR-0001 records planned `apps/ios-capture/`.
68. ADR-0001 records planned `apps/windows-studio/`.
69. ADR-0001 records planned `core/`.
70. ADR-0001 records planned `schemas/`.
71. ADR-0001 records planned `assets/`, `tests/`, and `tools/`.
72. ADR-0001 records `docs/architecture/` and `coordination/sessions/`.
73. ADR-0001 explicitly does not physically create the future PL-0019 application/core/schema/assets/tests/tools tree.
74. ADR-0001 keeps reusable Python/domain/application logic separate from PySide6 widget ownership.
75. ADR-0001 keeps cross-platform machine contracts at the future `schemas/` boundary.
76. ADR-0001 keeps coordination evidence separate from product/runtime source.
77. ADR-0001 preserves GitHub `main` as repository truth and root `TASKS.md` as live project-state truth.
78. ADR-0001 preserves the PL-0001 Scan/reference vs editable Design Model ownership direction.

## H. Rationale and alternatives

79. Rationale includes coordinated Capture/Studio evolution around PackScan.
80. Rationale includes atomic cross-platform contract changes.
81. Rationale includes one auditable architecture/history surface.
82. Rationale includes shared documentation/fixtures/tooling benefits.
83. Rationale addresses the single-owner/personal-project context without claiming that a monorepo is universally superior.
84. Alternative 1 evaluates separate iOS and Windows repositories.
85. Alternative 2 evaluates multiple repositories split by subsystem/core.
86. Alternative 3 evaluates a single repository without explicit ownership boundaries.
87. Each alternative states why it was not selected for current PackLab rather than labeling it universally wrong.

## I. Consequences, trade-offs and invariants

88. Positive consequences include easier atomic schema/contract changes.
89. Positive consequences include centralized CI/documentation/audit history.
90. Negative consequences include repository growth and/or unrelated-change coupling risk.
91. Consequences identify the later need for path-scoped CI and clear module ownership.
92. Consequences include public-repository privacy discipline for scans/supplier assets.
93. ADR-0001 does not imply every runtime/dependency must be installed for every subproject.
94. Invariants preserve UI-not-domain-truth.
95. Invariants preserve NextLevel behind PackLab-owned capture interfaces.
96. Invariants preserve external engines behind PackLab adapters/capability boundaries.
97. Invariants preserve Scan Mesh/Scan Master as reference rather than editable CAD truth.
98. Invariants preserve Design Model may derive from Scan Master but must not mutate it.
99. Invariants preserve Blender/render output is not dimensional truth.
100. Invariants preserve private Kenya/supplier data exclusion from the public source tree unless explicitly approved as safe public fixture material.

## J. References, scope and evidence

101. ADR-0001 references `../REPOSITORY_STRUCTURE.md`.
102. ADR-0001 references `../GLOSSARY.md`.
103. Root `TASKS.md` is not modified by Codex.
104. `AGENTS.md`, `CLAUDE.md`, `IMPLEMENTATION_GUIDE.md`, repository structure, glossary, coordination policy/index, prior session evidence, root `AUDIT.md`, and `handoff.md` are not modified by Codex.
105. No application/source/schema/runtime implementation is added.
106. No PL-0004+ work is implemented opportunistically.
107. The actual Codex GitHub range contains only the two authorized ADR documents plus matching Codex log.
108. `git diff --check` is recorded as passing.
109. New-file content review uses `git add -N` + diff, staged diff, or another command that can actually see new untracked file contents.
110. Explicit checks cover ADR statuses/lifecycle.
111. Explicit checks cover required ADR sections.
112. Explicit checks cover permanent numbering and non-destructive supersession.
113. Explicit checks cover TASKS single-tracker authority.
114. Explicit checks cover README ADR-0001 index entry.
115. Explicit checks cover ADR-0001 Accepted status and monorepo areas.
116. Explicit checks cover alternatives and both positive/negative consequences.
117. Explicit checks cover PL-0001 invariants and required references.
118. Matching `CODEX_LOG_V01.md` exists.
119. Log corresponds to prompt V01 and criteria V01.
120. Log records synchronization, exact validation commands/results, expected outcomes, explicit failure conditions and failures/fixes.
121. Log records implementation commit and push/remote visibility evidence.
122. Codex handoff is `AWAITING_AUDIT` and does not self-assign PASS.
123. No secrets, credentials, signing material, private scans, supplier-confidential content or proprietary production artwork are committed.

## Audit evidence rule

Codex-run local Git/PowerShell checks are E1/E2 until independently reproducible by ChatGPT. ChatGPT must audit actual GitHub files, commit range, ADR semantics, protected-file isolation, and architecture consistency directly.

A formally complete ADR template is not sufficient if ADR-0001 weakens the already audited PackLab ownership boundaries or quietly implements future folder/runtime work.

## Closure rule

ChatGPT may mark PL-0003 complete only when all 123 mandatory criteria pass and no material ambiguity remains.

If any mandatory criterion fails:

- PL-0003 remains unchecked;
- ChatGPT writes `CHATGPT_AUDIT_V01.md` with exact findings;
- ChatGPT updates root `TASKS.md` to `CHANGES_REQUIRED` or another truthful state;
- ChatGPT issues `CODEX_PROMPT_V02.md` and `CHATGPT_AUDIT_CRITERIA_V02.md`.
