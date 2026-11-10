# HISTORICAL CODEX GOAL — SUPERSEDED 2026-11-10

> **DO NOT EXECUTE THIS CODEX GOAL FOR NEW PACKLAB WORK.** The owner transferred exclusive execution, review and TASKS.md status ownership to **Claude Code** on 2026-11-10. Use [AUTONOMOUS_CLAUDE_GOAL.md](AUTONOMOUS_CLAUDE_GOAL.md) and root [CLAUDE.md](../CLAUDE.md). Prior Codex implementation/CI and peer review claims remain historical evidence, not new authorizations. The historical material below is preserved for traceability.

---

# PackLab CODEX: Execute all remaining tasks continuously

Owner authorization: 2026-11-04
Repo: `Sekiph82/PackLab` | Branch `main`
Local path: `C:\Users\sekip\Desktop\PackLab`

You are the PackLab Codex orchestrator for ALL unfinished root `TASKS.md` PL tasks. Read `AGENTS.md`, `coordination/AUTONOMOUS_EXECUTION_POLICY.md`, current `TASKS.md`, prior audits and actual source before work. The owner now authorizes continuous task selection, Codex-written tracker updates, project-wide cross-milestone progress, delegated subagents and GitHub Actions. Old stop-after-each-task and October Actions prohibitions no longer apply; factual physical/legal/test requirements are not waived.

Start with PL-0354: attempt the actual final-revision **full 205-method iOS XCTest** using GitHub-hosted macOS and inspect complete results. Repair failures and retest. If CI billing/runner remains unavailable, record `EXTERNAL_PENDING_CI`, do not fake a PASS and immediately move to another dependency-independent unchecked PL ID.

For every task: derive explicit acceptance criteria from task/technical contracts; implement; run focused/negative/regression tests and relevant Windows/macOS Actions; assign non-overlapping builder/tester/reviewer/security subagents; have a non-implementing reviewer actually inspect source diff and tests; fix any findings. Record exact commands, SHAs, CI links, observed results, privacy/license/safety review, limitations, review-agent evidence and acceptance in append-only `coordination/sessions/` files. Do not forge ChatGPT audits; use `CODEX_PEER_REVIEW_*.md`. Only real reviewed/tested passes may become `[x] AUTO_AUDITED_PASS` in root `TASKS.md`.

After EACH pass: commit scoped source/tests/evidence and `TASKS.md`; push `origin/main`; verify remote; safely sync and verify `C:\Users\sekip\Desktop\PackLab` when compatible; preserve dirty owner edits, and record `LOCAL_SYNC_PENDING` instead of claiming sync if unsafe; refresh `tools/dev/post_codex_owner_dev_refresh.ps1` for relevant Windows app changes. Select next independent task without waiting for ChatGPT. If blocked by real printer/phone/owner account/Apple signing/legal/supplier/hosted CI, keep that row unchecked with exact unblock condition; continue elsewhere. Never claim a real device, physical measurement, external license or factory/public release passed without evidence. Do not delete protected files, force-reset, force-push, run broad cleans or modify account billing/credentials.

Keep going within session limits, persist resume point in TASKS on exit, never promise that a background daemon exists unless one actually does. Report only verified achievements, current task and unresolved external gates.

**Canonical sync helper:** after each accepted and pushed PL task, run `tools/dev/post_task_safe_sync.ps1` against the owner Desktop checkout, inspect its SHA parity output, and log `LOCAL_SYNC_PENDING` if it refuses due to owner edits/divergence. Only use its `-RefreshOwnerDev` switch when native Windows runtime deployment is relevant; verify actual result. Never bypass its safe prechecks.
