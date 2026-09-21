# PL-0049 — ChatGPT Strict Audit Criteria V01

Task: **PL-0049 — CoreMotion metadata and synchronization**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V01.md

All **18 criteria** are mandatory.

1. TASKS.md authorized M02-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No M03 or unrelated future-milestone work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Actual changed files stay within the authorized child scope plus only justified minimal adjacent files.
7. Define CoreMotion attitude/rotation-rate/optional acceleration metadata with units and axis convention is satisfied.
8. Freeze timestamp domain and synchronization rules relative to capture/photo timestamps, including interpolation/nearest-sample policy and tolerance is satisfied.
9. Represent missing/stale/out-of-window motion data explicitly is satisfied.
10. Do not claim synchronization precision finer than the recorded clocks/evidence support is satisfied.
11. Add fixtures for aligned, stale and missing motion samples is satisfied.
12. Positive, negative and boundary evidence is meaningful and would detect a broken implementation.
13. Relevant accepted M00/M01 behavior and ownership boundaries remain unregressed.
14. Units, versions, coordinate conventions and provenance are explicit wherever dimensional/contract truth is involved.
15. git diff --check passes and builder TASKS.md diff is empty.
16. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
17. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_LOG_V01.md, links prompt/criteria, records implementation evidence and ends READY_FOR_INDEPENDENT_AUDIT.
18. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual GitHub implementation/evidence. Builder validation never self-closes this task.
