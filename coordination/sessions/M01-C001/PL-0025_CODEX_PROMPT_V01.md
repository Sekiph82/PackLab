# PL-0025 — Codex Child Work Order V01

Task: **PL-0025 — Create root task-runner strategy**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_LOG_V01.md

## Authority and synchronization

Read root TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, relevant M00 architecture/governance documents, and all artifacts produced by earlier M01 children that this task depends on.

TASKS.md must still authorize `M01-BATCH-001` / `CODEX`.

Before material work run and record:
`git fetch origin main --prune`
`git rev-list --left-right --count HEAD...origin/main`
`git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work.

## Authorized outputs

- `tools/tasks.py`
- `docs/development/TASK_RUNNER.md`

Additional minimal adjacent files are allowed only when technically necessary to make the authorized output valid, and every such file must be justified in the log.

## Mandatory requirements

1. Provide one documented cross-platform entry point for common bootstrap, test, lint, type-check, diagnostics and build-oriented commands.
2. Use explicit subprocess argument arrays and safe exit-code propagation; no shell-string execution for routine commands.
3. Commands not yet implemented by the current milestone must fail clearly or report deferred/unavailable rather than pretend success.
4. Keep the runner thin: it orchestrates owned tools and must not become domain truth or a second task tracker.
5. Add self-help/listing behavior and focused tests where practical.

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

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_LOG_V01.md with start commit, implementation/evidence commit, full prompt/criteria URLs, files read/changed, exact validation evidence, failures/fixes, scope/privacy review, platform limitations and remote visibility.

End the child log with `READY_FOR_INDEPENDENT_AUDIT`. Do not predeclare the future log commit SHA.
