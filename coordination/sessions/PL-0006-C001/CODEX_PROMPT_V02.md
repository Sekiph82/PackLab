# PL-0006-C001 — Codex Remediation Prompt V02

Status: **ISSUED**

Task: **PL-0006 — semantic versioning policy**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Purpose

V01 substantive implementation is accepted by audit. Do **not** rewrite `docs/architecture/VERSIONING_POLICY.md` unless a genuine new defect is discovered.

V02 exists because V01 failed one frozen synchronization criterion: the initial pre-material fetch did not use the exact required `git fetch origin main --prune` command.

## Mandatory startup

Read:

1. `AGENTS.md`
2. root `TASKS.md`
3. `coordination/sessions/PL-0006-C001/CODEX_PROMPT_V01.md`
4. `coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_CRITERIA_V01.md`
5. `coordination/sessions/PL-0006-C001/CODEX_LOG_V01.md`
6. `coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_V01.md`
7. this V02 prompt
8. `coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_CRITERIA_V02.md`

Root `TASKS.md` must show PL-0006 as current and `CHANGES_REQUIRED`. Otherwise STOP with `TASK_STATE_MISMATCH`.

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
- If local is only behind, run `git merge --ff-only origin/main`.
- Do not reset, rebase, force-push, use destructive checkout, silently stash, or run `git clean`.
- Before V02 validation begins, prove local HEAD equals `origin/main` and ahead/behind equals `0 0`.

After any fast-forward, rerun:

```powershell
git rev-list --left-right --count HEAD...origin/main
git rev-parse HEAD
git rev-parse origin/main
```

## Phase 1 — revalidate accepted V01 policy

Read and validate:

`docs/architecture/VERSIONING_POLICY.md`

Do not change it unless a new factual or architectural defect is discovered.

Confirm at minimum:

- StudioVersion, CaptureVersion, and PackScanSchemaVersion remain independent and not numerically locked;
- Studio/Capture MAJOR/MINOR/PATCH semantics remain correct;
- PackScan schema MAJOR/MINOR/PATCH semantics remain conservative and explicit;
- compatibility matrix cases remain present;
- reader/writer contracts remain explicit;
- migration remains explicit, versioned, non-destructive, and failure-safe;
- future application-to-schema compatibility declarations remain defined;
- Git SHA remains provenance, not semantic version;
- `.packscan` immutability, millimetres, coordinate semantics, and Scan Mesh / Scan Master / Design Model separation remain intact;
- no release implementation, schema implementation, app version file, tag, workflow, manifest, or PL-0007+ work is introduced.

Run:

```powershell
git diff --check
```

and protected-scope checks proving no unauthorized tracked file is changed.

## Authorized changes

If the existing policy is still correct, add exactly one file:

`coordination/sessions/PL-0006-C001/CODEX_LOG_V02.md`

Do not modify:

- `docs/architecture/VERSIONING_POLICY.md` unless a newly discovered real defect requires correction;
- `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- prior prompt/criteria/log/audit files;
- application/source/schema/runtime files;
- release/tag/workflow/manifest/package/lock files.

Do not begin PL-0007.

## Required V02 log

Write `CODEX_LOG_V02.md` and include:

- prompt/criteria paths;
- exact synchronization commands and raw results;
- pre-merge ahead/behind relation;
- whether a merge was required;
- final `0 0` relation and equal HEAD/origin/main before V02 material validation;
- policy revalidation checks/results;
- protected-file/scope result;
- files changed;
- failures/fixes;
- push and remote visibility evidence;
- final `AWAITING_AUDIT`.

Do not predeclare the future commit SHA containing the final log.

## Commit / push

Commit and push only the authorized V02 evidence artifact, plus a policy correction only if a genuine newly discovered defect requires it.

## Final response

Return only:

- `PL-0006-C001 V02`;
- GitHub path/URL to `CODEX_LOG_V02.md`;
- `AWAITING_AUDIT`.

Then STOP.
