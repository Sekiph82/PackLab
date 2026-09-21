# PL-0066 — ChatGPT Strict Audit Criteria V01

Task: **PL-0066 — Calibration profile storage and invalidation**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V01.md

All **18 criteria** are mandatory.

1. TASKS.md authorized M02-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No M03 or unrelated future-milestone work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Actual changed files stay within the authorized child scope plus only justified minimal adjacent files.
7. Implement a versioned calibration-profile model keyed by device/lens/resolution and required capture/calibration conditions is satisfied.
8. Define deterministic compatibility checks and invalidate profiles on incompatible device/lens/resolution/model/version changes is satisfied.
9. Store units, provenance, creation/verification timestamps and calibration-quality evidence is satisfied.
10. Never silently reuse a profile when compatibility cannot be established is satisfied.
11. Add tests for exact match, compatible reuse where explicitly allowed, and every invalidation dimension is satisfied.
12. Positive, negative and boundary evidence is meaningful and would detect a broken implementation.
13. Relevant accepted M00/M01 behavior and ownership boundaries remain unregressed.
14. Units, versions, coordinate conventions and provenance are explicit wherever dimensional/contract truth is involved.
15. git diff --check passes and builder TASKS.md diff is empty.
16. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
17. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_LOG_V01.md, links prompt/criteria, records implementation evidence and ends READY_FOR_INDEPENDENT_AUDIT.
18. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual GitHub implementation/evidence. Builder validation never self-closes this task.
