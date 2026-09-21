# PL-0034 — Codex Remediation Work Order V02

Task: **PL-0034 — CUDA capability provenance remediation**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_V01.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `core/src/packlab_core/capabilities.py`
- `tests/core/test_capabilities.py`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. Separate NVIDIA driver/NVML discovery from CUDA runtime/toolkit capability truth.
2. Do not mark CUDA AVAILABLE merely because nvidia-smi exists or returns a generic version.
3. CUDA AVAILABLE must require direct evidence of the intended CUDA capability with explicit provenance; otherwise use UNKNOWN or UNAVAILABLE conservatively.
4. Never infer CUDA from GPU name, memory, AdapterRAM, or generic version parsing.
5. Preserve missing/probe-error isolation and the unselected Python OpenCascade binding.
6. Add tests proving nvidia-smi alone does not establish CUDA, direct CUDA evidence can establish it, and malformed/missing probes stay conservative.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
