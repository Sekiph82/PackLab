# PL-0024 — Codex Remediation Work Order V02

Task: **PL-0024 — Environment diagnostics GPU discovery remediation**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_V01.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `tools/environment_report.py`
- `tests/tools/test_environment_report.py`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. Add safe cross-platform GPU adapter discovery, with a Windows path that can report non-NVIDIA adapters such as Intel Iris Xe.
2. Keep generic GPU adapter discovery separate from CUDA evidence.
3. Do not infer CUDA, dedicated VRAM, or compute capability from AdapterRAM, GPU name, generic memory fields, or mere adapter presence.
4. Preserve safe timeouts, shell=False, no installation/system mutation, deterministic missing/error states, structured JSON and privacy omissions.
5. Add injected/fake tests for a non-NVIDIA Windows adapter, NVIDIA adapter metadata without automatic CUDA proof, missing probes, and privacy/redaction.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
