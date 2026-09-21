# M02-C001 — Master Codex Work Order V01

Repository: https://github.com/Sekiph82/PackLab
Milestone: **M02 — PackScan Data Contract & Calibration**
Tasks: **PL-0044 through PL-0068**

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization gate

Root TASKS.md must show:
- Current Milestone: M02
- Current Task: M02-BATCH-001
- Current Task Status: READY
- Required Actor: CODEX
- Next action pointing to this master prompt

Otherwise stop with `TASK_STATE_MISMATCH`.

## Execution model

Execute the following child work orders sequentially. Every child keeps its own implementation/evidence commit and child log. Continue only while the current child is validation-green and no stop condition exists.

1. PL-0044 — Versioned PackScan ZIP container layout
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CHATGPT_AUDIT_CRITERIA_V01.md
2. PL-0045 — PackScan manifest.json JSON Schema
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CHATGPT_AUDIT_CRITERIA_V01.md
3. PL-0046 — Per-photo metadata schema
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_CRITERIA_V01.md
4. PL-0047 — Camera intrinsics representation
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_CRITERIA_V01.md
5. PL-0048 — ARKit pose representation
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V01.md
6. PL-0049 — CoreMotion metadata and synchronization
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_CRITERIA_V01.md
7. PL-0050 — Optional object-mask contract
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CHATGPT_AUDIT_CRITERIA_V01.md
8. PL-0051 — Calibration marker observations and millimetre units
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0051_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0051_CHATGPT_AUDIT_CRITERIA_V01.md
9. PL-0052 — Capture-mode metadata
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0052_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0052_CHATGPT_AUDIT_CRITERIA_V01.md
10. PL-0053 — Preview thumbnail and diagnostics payload contract
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CHATGPT_AUDIT_CRITERIA_V01.md
11. PL-0054 — SHA-256 integrity and corrupt-package handling
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0054_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0054_CHATGPT_AUDIT_CRITERIA_V01.md
12. PL-0055 — PackScan validation fixture corpus
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0055_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0055_CHATGPT_AUDIT_CRITERIA_V01.md
13. PL-0056 — Python PackScan reader writer validator
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CHATGPT_AUDIT_CRITERIA_V01.md
14. PL-0057 — Swift PackScan writer
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_CRITERIA_V01.md
15. PL-0058 — Cross-language PackScan contract tests
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CHATGPT_AUDIT_CRITERIA_V01.md
16. PL-0059 — Calibration marker family and IDs
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0059_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0059_CHATGPT_AUDIT_CRITERIA_V01.md
17. PL-0060 — Printable A4/A3 calibration mat design
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CHATGPT_AUDIT_CRITERIA_V01.md
18. PL-0061 — Printed-mat physical verification procedure
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CHATGPT_AUDIT_CRITERIA_V01.md
19. PL-0062 — OpenCV marker detection and corner refinement
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V01.md
20. PL-0063 — Scale estimation from known marker geometry
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CHATGPT_AUDIT_CRITERIA_V01.md
21. PL-0064 — Calibration confidence and rejection thresholds
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_CRITERIA_V01.md
22. PL-0065 — iPhone main-camera calibration procedure
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CHATGPT_AUDIT_CRITERIA_V01.md
23. PL-0066 — Calibration profile storage and invalidation
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_CRITERIA_V01.md
24. PL-0067 — Synthetic calibration ground-truth tests
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CHATGPT_AUDIT_CRITERIA_V01.md
25. PL-0068 — First physical calibration benchmark
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_PROMPT_V01.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CHATGPT_AUDIT_CRITERIA_V01.md

## Hard boundaries

- Never edit root TASKS.md.
- Never create ChatGPT audit verdict files.
- Never self-assign AUDITED_PASS.
- Never start M03.
- Preserve M00/M01 accepted architecture and privacy boundaries.
- PackScan schemas in `schemas/` are cross-platform contract truth; Swift/UI/external libraries must not become contract truth.
- Use millimetres for physical calibration truth unless a schema field explicitly represents a different unit.
- Do not fabricate Xcode/device/CUDA/physical measurement evidence.
- Private captures, Kenya packaging scans, confidential supplier material and credentials stay out of public Git.

## PL-0068 owner gate

PL-0068 requires real physical benchmark evidence. If real owner-supplied mat verification/capture/measurement evidence is unavailable, do not invent it. Record the owner gate in PL-0068_CODEX_LOG_V01.md, create the master log with `BATCH_STOPPED_OWNER_REQUIRED`, push only authorized evidence, and stop.

## Master handoff

After PL-0068 completes or the owner gate stops the batch, publish:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_LOG_V01.md

Index every attempted child with prompt/criteria/log URL, synchronized start, implementation/evidence commit, child-log commit, files changed, validations, limitations and final state.

Successful full completion ends:
`M02_BATCH_COMPLETED`
`AWAITING_MILESTONE_AUDIT`

Owner-gated stop ends:
`BATCH_STOPPED_OWNER_REQUIRED`
`AWAITING_MILESTONE_AUDIT`

Do not continue to M03.
