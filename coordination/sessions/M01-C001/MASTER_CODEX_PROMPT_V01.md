# M01-C001 — PackLab M01 Full Milestone Master Codex Work Order V01

Milestone: **M01 — Monorepo & Development Foundations**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Execute every M01 child **PL-0019 through PL-0043** sequentially in one owner-authorized milestone batch.

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Batch protocol:
https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md

Master criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization gate

Before work, TASKS.md must show:
- Current Milestone: M01
- Current Task: M01-BATCH-001
- Current Task Status: READY
- Required Actor: CODEX

Otherwise stop with `TASK_STATE_MISMATCH`.

## Initial synchronization

Run:
`git fetch origin main --prune`
`git rev-list --left-right --count HEAD...origin/main`
`git status --porcelain`

Use fast-forward-only synchronization if behind-only and clean. Stop on tracked changes, ahead/diverged state, unsafe collision or authorization mismatch. Never reset/rebase/force-push/destructively clean/silent-stash.

## Frozen child order

1. PL-0019 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0019_CODEX_PROMPT_V01.md
2. PL-0020 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0020_CODEX_PROMPT_V01.md
3. PL-0021 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0021_CODEX_PROMPT_V01.md
4. PL-0022 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0022_CODEX_PROMPT_V01.md
5. PL-0023 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0023_CODEX_PROMPT_V01.md
6. PL-0024 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V01.md
7. PL-0025 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_PROMPT_V01.md
8. PL-0026 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V01.md
9. PL-0027 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0027_CODEX_PROMPT_V01.md
10. PL-0028 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0028_CODEX_PROMPT_V01.md
11. PL-0029 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0029_CODEX_PROMPT_V01.md
12. PL-0030 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CODEX_PROMPT_V01.md
13. PL-0031 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V01.md
14. PL-0032 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0032_CODEX_PROMPT_V01.md
15. PL-0033 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0033_CODEX_PROMPT_V01.md
16. PL-0034 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_PROMPT_V01.md
17. PL-0035 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V01.md
18. PL-0036 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_PROMPT_V01.md
19. PL-0037 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CODEX_PROMPT_V01.md
20. PL-0038 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0038_CODEX_PROMPT_V01.md
21. PL-0039 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0039_CODEX_PROMPT_V01.md
22. PL-0040 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0040_CODEX_PROMPT_V01.md
23. PL-0041 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CODEX_PROMPT_V01.md
24. PL-0042 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0042_CODEX_PROMPT_V01.md
25. PL-0043 — https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V01.md

For each child, read its matching locked criteria:
`https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-xxxx_CHATGPT_AUDIT_CRITERIA_V01.md`

Execute one child at a time. Every child gets:
1. its own implementation/evidence boundary;
2. its own focused validation/regression evidence;
3. its own log at `coordination/sessions/M01-C001/PL-xxxx_CODEX_LOG_V01.md`;
4. a log-only publication boundary where practical;
5. remote visibility verification.

After each child push, refresh from origin and require safe `0 0` before starting the next.

## Batch stop rule

Stop the entire batch at the first child that cannot satisfy frozen requirements because of a defect, blocker, owner decision, platform requirement, architecture contradiction, privacy/security issue or unsafe repository state.

Do not skip a failed/blocked child. Do not start later children. Publish honest `BATCH_STOPPED` master evidence.

## Hard boundaries

- Never edit TASKS.md.
- Never create ChatGPT audit files.
- Never mark tasks complete.
- Never start M02.
- Preserve M00 governance/architecture.
- Do not claim Windows-native Xcode evidence.
- Do not fabricate device, signing, CUDA, physical or external-tool evidence.
- Keep private scans/supplier data/secrets out of public Git.

## Master log

After all 25 child logs are published, create:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CODEX_LOG_V01.md

Index every child with prompt URL, criteria URL, synchronized start, implementation/evidence commit, log commit, log URL, changed files, validation result, failures/fixes and residual limitations.

Record initial/final repository state, protected TASKS.md review, M02-not-started proof, privacy/security review, and `BATCH_COMPLETED` or `BATCH_STOPPED`.

End with `AWAITING_MILESTONE_AUDIT`.

Final response only:
`M01-C001`
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CODEX_LOG_V01.md
`AWAITING_MILESTONE_AUDIT`
