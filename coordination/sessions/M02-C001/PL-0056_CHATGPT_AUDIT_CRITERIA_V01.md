# PL-0056 — ChatGPT Strict Audit Criteria V01

Task: **PL-0056 — Python PackScan reader writer validator**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_PROMPT_V01.md

All **19 criteria** are mandatory.

1. TASKS.md authorized M02-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No M03 or unrelated future-milestone work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Actual changed files stay within the authorized child scope plus only justified minimal adjacent files.
7. Implement Python PackScan read/write/validate APIs against the frozen M02 schemas and layout is satisfied.
8. Use safe ZIP handling with no path traversal, duplicate ambiguity or extraction outside owned temp paths is satisfied.
9. Produce deterministic package structure/checksums for equivalent logical input is satisfied.
10. Return structured validation errors for version, schema, checksum, missing, extra and corrupt cases is satisfied.
11. Do not mutate source packages during read/validate and do not weaken schema rules to make fixtures pass is satisfied.
12. Add focused tests across the full public fixture corpus is satisfied.
13. Positive, negative and boundary evidence is meaningful and would detect a broken implementation.
14. Relevant accepted M00/M01 behavior and ownership boundaries remain unregressed.
15. Units, versions, coordinate conventions and provenance are explicit wherever dimensional/contract truth is involved.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
18. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_LOG_V01.md, links prompt/criteria, records implementation evidence and ends READY_FOR_INDEPENDENT_AUDIT.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual GitHub implementation/evidence. Builder validation never self-closes this task.
