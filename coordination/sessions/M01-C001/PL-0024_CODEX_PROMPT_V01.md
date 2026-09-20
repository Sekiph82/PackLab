# PL-0024 — Codex Child Work Order V01

Task: **PL-0024 — Create local environment diagnostics script**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_LOG_V01.md

## Authority and synchronization

Read root TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, relevant M00 architecture/governance documents, and all artifacts produced by earlier M01 children that this task depends on.

TASKS.md must still authorize `M01-BATCH-001` / `CODEX`.

Before material work run and record:
`git fetch origin main --prune`
`git rev-list --left-right --count HEAD...origin/main`
`git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work.

## Authorized outputs

- `tools/environment_report.py`
- `tests/tools/test_environment_report.py`

Additional minimal adjacent files are allowed only when technically necessary to make the authorized output valid, and every such file must be justified in the log.

## Mandatory requirements

1. Report OS, architecture, CPU, logical/physical core information when safely available, RAM, GPU adapters, CUDA availability, Python version and discoverable external tool versions.
2. Treat integrated GPU memory fields conservatively and never equate AdapterRAM with dedicated VRAM or CUDA.
3. Probe capabilities safely with timeouts and no installation or system mutation.
4. Redact or avoid usernames, home paths, machine identifiers, serial numbers, tokens and other protected data.
5. Return structured machine-readable data plus readable terminal output and deterministic missing-tool states.
6. Add tests using injected/fake command results so diagnostics logic is testable without requiring every engine.

## Validation

Run all task-relevant focused tests/checks plus:
- `git diff --check`
- `git diff -- TASKS.md`
- exact changed-file review
- protected-file review
- privacy/secrets review
- relevant earlier-M01 regression checks.

For new files, use a diff/staged review that can actually see untracked content.

Platform-specific evidence must be truthful. Windows must not be represented as native Xcode/macOS. If a required validation is impossible without a future authorized platform, record the limitation and satisfy only the frozen criterion actually required here; never fabricate a pass.

## Boundaries

Do not edit TASKS.md. Do not self-audit. Do not create ChatGPT audit files. Do not start M02. Do not pull future PackScan/capture/reconstruction/CAD behavior into M01.

If this child cannot satisfy its frozen mandatory requirements safely, stop the entire M01 batch and publish the child/master stop evidence.

## Log and handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_LOG_V01.md with start commit, implementation/evidence commit, full prompt/criteria URLs, files read/changed, exact validation evidence, failures/fixes, scope/privacy review, platform limitations and remote visibility.

End the child log with `READY_FOR_INDEPENDENT_AUDIT`. Do not predeclare the future log commit SHA.
