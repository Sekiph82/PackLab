# PackLab Handoff Notes

> **Non-authoritative workflow aid.** Current project state is defined only by root `TASKS.md` on GitHub `main`.

This file must not contain the canonical current milestone, sprint, task, status, next action, required actor, project progress, or audit verdict.

## Canonical live state

Always read:

`TASKS.md`

The explicit `## Project Status` section is authoritative for H!veAI and all agents.

## Canonical implementation/audit evidence

Versioned work orders and evidence live under:

`coordination/sessions/<CYCLE_ID>/`

Normal bundle:

```text
CODEX_PROMPT_VNN.md
CHATGPT_AUDIT_CRITERIA_VNN.md
CODEX_LOG_VNN.md
CHATGPT_AUDIT_VNN.md
```

- Codex writes implementation/test evidence in the matching `CODEX_LOG_VNN.md`.
- ChatGPT performs the independent audit, writes `CHATGPT_AUDIT_VNN.md`, and updates root `TASKS.md` after every audit cycle.
- Failed audits receive a new versioned remediation prompt/criteria pair; prior versions remain history.

## Local workspace

`C:\Users\sekip\Desktop\PackLab`

GitHub `main` is repository truth. The owner has authorized one initial GitHub-authoritative local bootstrap; afterwards normal sessions use safe fetch/compare/fast-forward and stop on unexpected divergence unless the owner explicitly authorizes replacement.

## Notes policy

Temporary human notes may be added here only when they do not duplicate live state. Do not turn this file into a second tracker, queue or audit ledger.
