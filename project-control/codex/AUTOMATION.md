# SUPERSEDED — Codex autonomous queue retired

Since the 2026-11-10 owner handoff, Claude Code is the sole PackLab executor (see root
`CLAUDE.md`). This Codex automation is retired and must not run. The tracker-writing queue,
owner-answer inbox, dashboard and Codex App Server client were removed in the PL-0438 review
(`coordination/sessions/M16-C002/CLAUDE_PEER_REVIEW_PL0438_V01.md`). Only the read-only validators
`tools/codex/task_queue.py` and `scripts/codex/validate-task-state.mjs` remain. Root `TASKS.md` is
the only tracker; `jobs/*/job.json` are historical Codex evidence, not task status. The original
text is in git history.
