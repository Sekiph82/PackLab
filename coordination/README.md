# PackLab Coordination Protocol | Claude Code Handoff (2026-11-10)

## Active authority
Claude Code is sole new-work orchestrator and `TASKS.md` lifecycle author for all unfinished permanent PL tasks. GitHub `Sekiph82/PackLab` `main` is source truth; root `TASKS.md` is the only live tracker. Read `../CLAUDE.md`, `AUTONOMOUS_CLAUDE_GOAL.md` and `AUTONOMOUS_EXECUTION_POLICY.md`. The former ChatGPT-only, Codex-only, frozen-prompt-per-task and milestone-stop operating requirements are **superseded for new work**. Historical prompts, logs and audits under `coordination/sessions/` are immutable evidence, not a competing task tracker.

## Roles
- **Claude orchestrator:** owns dependency-aware scheduling, technical/CI work, milestone planning, independent subagent review requests, accepted status edits, Git publication, Desktop and OwnerDev synchronization.
- **Claude builder/dataset-curator:** implement assigned scopes with real tests; do not self-certify independent review.
- **Claude tester/reviewer/security:** examine real source and check/CI evidence independently, document findings; no claim of external/physical truth without observed data.
- **Owner:** supplies only genuinely owner-exclusive facts/decisions, such as physical printer/sample, Apple signing credentials, account/billing changes or formal legal/factory approval; lack of these does not stop independent software work.
- **Codex/ChatGPT:** all prior outputs are preserved as historical evidence. They are no longer the mandatory next executor or sole tracker writer.

## Execution loop
1. Read current `TASKS.md`; inventory every unchecked PL ID and actual contract/dependencies. Start from the live frontier (PL-0369 at handoff), not outdated PL-0354 references.
2. Build 3–5 related executable tasks when safe, trace IDs individually; use focused verification during development.
3. Run all mandatory regression/hosted Windows/macOS suites before corresponding milestone/criterion acceptance; inspect actual pass/fail results.
4. Independent Claude peer/source/security review; remediate defects. Save new `CLAUDE_IMPLEMENTATION_LOG_*.md` and `CLAUDE_PEER_REVIEW_*.md` under versioned session folders, NEVER forged `CHATGPT_AUDIT_*` or `CODEX_PEER_REVIEW_*`.
5. Only genuinely verified work becomes `[x] CLAUDE_PEER_AUDITED_PASS`. External gates remain `[ ] EXTERNAL_PENDING_*` and are re-entered after evidence arrives while independent tasks proceed.
6. Per truly accepted task: commit and push GitHub `main`, verify SHA; safely fast-forward Desktop through `tools/dev/post_task_safe_sync.ps1`, record actual local parity or `LOCAL_SYNC_PENDING`; refresh OwnerDev when relevant; continue task selection.

## Real-data and safety boundary
Kenya factory and authentic production scans do not yet exist. Claude creates rights-cleared genuine public and reproducible physically credible SYNTHETIC proxy datasets for software testing, not fabricated Kenya or physical acceptance. Private inputs stay outside Git. GitHub repository currently PUBLIC. Preserve real architecture, product/security/licensing, owner-owned files, device/physical/legal acceptance and privacy. GitHub Actions are allowed but should not be run wastefully or with false PASS claims.

No second project-status ledger; older `AUDIT.md`, `handoff.md`, archived sessions, audit index and historical Codex goal remain non-authoritative references.
