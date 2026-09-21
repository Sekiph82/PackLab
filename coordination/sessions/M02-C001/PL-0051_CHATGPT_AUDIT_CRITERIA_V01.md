# PL-0051 — ChatGPT Strict Audit Criteria V01

Task: **PL-0051 — Calibration marker observations and millimetre units**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0051_CODEX_PROMPT_V01.md

All **18 criteria** are mandatory.

1. TASKS.md authorized M02-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No M03 or unrelated future-milestone work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Actual changed files stay within the authorized child scope plus only justified minimal adjacent files.
7. Define calibration-marker observations with marker family/dictionary, ID, image corners, confidence/quality and known geometry is satisfied.
8. Use millimetres as the canonical real-world unit and state conversion/precision rules explicitly is satisfied.
9. Record provenance for known marker dimensions and reject unitless scale values is satisfied.
10. Represent partial/ambiguous marker observations without promoting them to valid scale truth is satisfied.
11. Add fixtures for valid multi-marker observations, partial observations and invalid unit/geometry data is satisfied.
12. Positive, negative and boundary evidence is meaningful and would detect a broken implementation.
13. Relevant accepted M00/M01 behavior and ownership boundaries remain unregressed.
14. Units, versions, coordinate conventions and provenance are explicit wherever dimensional/contract truth is involved.
15. git diff --check passes and builder TASKS.md diff is empty.
16. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
17. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0051_CODEX_LOG_V01.md, links prompt/criteria, records implementation evidence and ends READY_FOR_INDEPENDENT_AUDIT.
18. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual GitHub implementation/evidence. Builder validation never self-closes this task.
