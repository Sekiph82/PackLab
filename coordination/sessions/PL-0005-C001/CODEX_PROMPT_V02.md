# PL-0005-C001 — Codex Remediation Prompt V02

Status: **ISSUED**

Task: **PL-0005 — dependency/license register**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Purpose

V01 substantive implementation is accepted by audit. Do **not** rewrite `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` unless a new defect is discovered.

V02 exists only because V01 failed two frozen synchronization-evidence criteria:

- pre-implementation fetch did not include `--prune`;
- explicit ahead/behind evidence was not recorded before merge.

## Mandatory startup

Read:

1. `AGENTS.md`
2. root `TASKS.md`
3. `coordination/sessions/PL-0005-C001/CODEX_PROMPT_V01.md`
4. `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_CRITERIA_V01.md`
5. `coordination/sessions/PL-0005-C001/CODEX_LOG_V01.md`
6. `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_V01.md`
7. this V02 prompt
8. `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_CRITERIA_V02.md`

Root `TASKS.md` must show PL-0005 as current and `CHANGES_REQUIRED`. Otherwise STOP with `TASK_STATE_MISMATCH`.

## Phase 0 — exact synchronization evidence

Before any material V02 validation work, run exactly:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- Verify Git root and origin identify `Sekiph82/PackLab`.
- Historical untracked `.hiveai/` may remain local but must not be staged.
- If tracked changes exist, STOP.
- If local is ahead or diverged, STOP.
- If local is only behind, run `git merge --ff-only origin/main`, then rerun:

```powershell
git rev-list --left-right --count HEAD...origin/main
git rev-parse HEAD
git rev-parse origin/main
```

- Do not reset, rebase, force-push, destructive checkout, silent stash, or `git clean`.
- Before V02 validation begins, prove local HEAD equals `origin/main` and ahead/behind is `0 0`.

## Phase 1 — revalidate accepted V01 artifact

Do not change the register unless a real new defect is found.

Read and validate:

`docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

Confirm at minimum:

- all required dependency entries still exist;
- OpenMVS remains AGPL-3.0 / HIGH LICENSE ATTENTION;
- COLMAP third-party licensing caveat remains present;
- OpenCV version-sensitive license split remains present;
- PyTorch main-project vs installed-package/transitive distinction remains present;
- OCCT and Python binding licenses remain separate;
- Python OpenCascade binding remains `TBD / NOT SELECTED` and PL-0289 retains selection ownership;
- Blender software/output distinction remains present;
- PySide6/Qt licensing-route/module sensitivity remains present;
- no dependency is newly installed, pinned or distribution-cleared by this task;
- no legal conclusion beyond the documented conservative governance register is introduced.

Run:

```powershell
git diff --check
```

and a protected-scope check proving no unauthorized tracked files were changed.

## Authorized changes

If the existing register is still correct, add exactly one file:

`coordination/sessions/PL-0005-C001/CODEX_LOG_V02.md`

Do not modify:

- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` unless a newly discovered factual defect requires correction;
- root `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- prior prompt/criteria/log/audit files;
- application/source/schema/runtime files.

Do not begin PL-0006.

## Required V02 log

Write `CODEX_LOG_V02.md` and include:

- prompt/criteria paths;
- exact synchronization commands and raw results;
- explicit pre-merge ahead/behind relation;
- whether merge was needed;
- proof of final `0 0` relation and equal HEAD/origin/main before V02 material validation;
- register revalidation checks/results;
- protected-file/scope result;
- files changed;
- any failures/fixes;
- implementation/log commit and remote visibility evidence;
- final `AWAITING_AUDIT`.

Do not predeclare the future commit SHA containing the final log.

## Commit / push

Commit and push only the authorized V02 evidence artifact, plus a register correction only if a newly discovered factual defect genuinely requires it.

## Final response

Return only a concise handoff containing:

- `PL-0005-C001 V02`;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP.
