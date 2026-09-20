# M01-C001 — ChatGPT Master Strict Audit Criteria V01

Milestone: **M01 — Monorepo & Development Foundations**
Children: **PL-0019 through PL-0043**
Repository: https://github.com/Sekiph82/PackLab

All criteria are mandatory.

## Batch governance
1. TASKS.md explicitly authorized M01-BATCH-001 / READY / CODEX before implementation.
2. The batch covers exactly PL-0019 through PL-0043 in frozen order.
3. Codex does not edit TASKS.md or create ChatGPT audit artifacts.
4. M00 accepted architecture/governance remains intact.
5. No M02 task is started.
6. Initial synchronization is safe and later children re-check origin freshness.
7. No destructive/unsafe Git shortcut is used.
8. Every child has a frozen prompt and locked criteria before its implementation.
9. Every child has a separate implementation/evidence boundary and child log.
10. The batch stops rather than skips any failed/blocked child.

## Child closure gates
11. PL-0019 independently passes its locked child criteria.
12. PL-0020 independently passes its locked child criteria.
13. PL-0021 independently passes its locked child criteria.
14. PL-0022 independently passes its locked child criteria.
15. PL-0023 independently passes its locked child criteria.
16. PL-0024 independently passes its locked child criteria.
17. PL-0025 independently passes its locked child criteria.
18. PL-0026 independently passes its locked child criteria.
19. PL-0027 independently passes its locked child criteria.
20. PL-0028 independently passes its locked child criteria.
21. PL-0029 independently passes its locked child criteria.
22. PL-0030 independently passes its locked child criteria.
23. PL-0031 independently passes its locked child criteria.
24. PL-0032 independently passes its locked child criteria.
25. PL-0033 independently passes its locked child criteria.
26. PL-0034 independently passes its locked child criteria.
27. PL-0035 independently passes its locked child criteria.
28. PL-0036 independently passes its locked child criteria.
29. PL-0037 independently passes its locked child criteria.
30. PL-0038 independently passes its locked child criteria.
31. PL-0039 independently passes its locked child criteria.
32. PL-0040 independently passes its locked child criteria.
33. PL-0041 independently passes its locked child criteria.
34. PL-0042 independently passes its locked child criteria.
35. PL-0043 independently passes its locked child criteria.

## Cross-child coherence
36. The physical monorepo matches REPOSITORY_STRUCTURE.md ownership boundaries.
37. Root README, ignore rules, line-ending policy, generated-artifact/LFS policy and cache policy are mutually consistent.
38. Environment diagnostics, task runner, Python pin, package layout, lock/bootstrap and quality/test tooling are mutually consistent.
39. packlab_core remains independent from PySide6 presentation.
40. Python configuration, logging, capability registry and subprocess runner compose without circular truth ownership.
41. The deferred Python OCCT binding remains unselected.
42. The iOS foundation is SwiftUI/NextLevel/ARKit-ready without requiring LiDAR or Pro-only hardware.
43. NextLevel remains behind PackLab-owned camera interfaces and its pin/provenance is explicit.
44. Swift concurrency/warning settings, permissions, diagnostics, simulator fallback and test target are coherent.
45. Windows/macOS platform evidence is represented truthfully and unavailable Xcode/device evidence is not fabricated.
46. No secret/private scan/supplier/signing material or unsafe generated artifact is committed.
47. No child creates a second live tracker or redefines schema/domain truth that belongs to later milestones.

## Master publication
48. MASTER_CODEX_LOG_V01.md exists and indexes all 25 children.
49. Master log accurately records BATCH_COMPLETED or BATCH_STOPPED.
50. If stopped, no later child starts after the stop frontier.
51. If completed, all child logs and implementation boundaries are remotely visible.
52. Actual GitHub diffs/commits match the master log claims.
53. Final protected-file review proves Codex did not modify TASKS.md.
54. Final review proves M02 was not started.
55. Master log ends AWAITING_MILESTONE_AUDIT and does not self-assign milestone acceptance.

## Closure

ChatGPT audits every child separately and writes a distinct `PL-xxxx_CHATGPT_AUDIT_V01.md` after each audit. Only after child audits close does ChatGPT write the milestone audit and update TASKS.md.

If any child fails, M01 remains open at that remediation frontier; already accepted sibling audits remain valid unless new evidence invalidates them.
