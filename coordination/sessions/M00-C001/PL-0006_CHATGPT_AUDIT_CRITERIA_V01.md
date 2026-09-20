# PL-0006 - ChatGPT Strict Child Audit Criteria V01

Task: **PL-0006 - Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_LOG_V01.md

All 30 criteria are mandatory.

1. M00-BATCH-001/CODEX authorization existed before child work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked before the child.
5. No unsafe Git operation was used.
6. No secret/private/confidential artifact entered public Git.
7. Prior prompt/log/audit history was not rewritten.
8. VERSIONING_POLICY.md was revalidated against current repository truth.
9. The policy was not rewritten merely to manufacture a diff.
10. If changed, a genuine substantive defect was documented before correction; if unchanged, exact unchanged status was proven.
11. StudioVersion, CaptureVersion and PackScanSchemaVersion remain separate domains.
12. Studio/Capture SemVer MAJOR/MINOR/PATCH, prerelease and 0.y.z semantics remain explicit.
13. PackScan schema MAJOR/MINOR/PATCH compatibility semantics remain explicit and conservative.
14. Required-field/unit/coordinate/checksum/orientation/calibration breaking changes cannot hide in PATCH.
15. Older/newer Studio/Capture/schema compatibility cases remain explicitly covered.
16. Compatibility is capability/version checked rather than guessed.
17. Unsupported future schema MAJOR is rejected cleanly.
18. Reader behavior forbids silent reinterpretation of units, coordinate frames, checksums, orientation, calibration and required file semantics.
19. Writer behavior cannot emit semantics beyond its declared schema version.
20. Migrations remain explicit, versioned, source/target bound and non-destructive.
21. Lossy migration remains explicit and audit/user visible.
22. Future application releases still declare schema read/write/migration compatibility.
23. PL-0363/PL-0364 retain release numbering/manifest ownership.
24. Immutable .packscan evidence, millimetres and explicit coordinate semantics remain preserved.
25. Scan Mesh / Scan Master / Design Model separation remains intact.
26. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
27. Actual changed files match child authorization and protected-file/privacy reviews pass.
28. Child log records start/implementation evidence, validations, failures/fixes, scope/privacy and push evidence.
29. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
30. Actual GitHub diff/source matches the child log claims.

## Closure

ChatGPT independently inspects the actual GitHub commit range, artifact semantics, child log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0006 unaccepted and M00 open.
