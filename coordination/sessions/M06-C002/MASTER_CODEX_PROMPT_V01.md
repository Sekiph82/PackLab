# M06-BATCH-002 — Codex Continuation Work Order V01

Milestone: **M06 — PackLab Studio Foundation**  
Tasks: **PL-0150 through PL-0157**  
Repository: https://github.com/Sekiph82/PackLab  
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Prior R01 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_V01.md

Required final master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_LOG_V01.md

## Authorization gate

Before material work, read:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

It must show:
- Current Milestone: M06
- Current Sprint: M06-BATCH-002
- Current Task: PL-0150 through PL-0157
- Current Task Status: READY
- Required Actor: CODEX
- PL-0135 through PL-0149 checked/accepted
- PL-0068 still OWNER_REQUIRED
- M07 not started
- Next Task/Action pointing to this prompt and criteria

Otherwise stop with `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git status --porcelain`
- `git rev-list --left-right --count HEAD...origin/main`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or discard owner work.

Never edit root `TASKS.md` or any ChatGPT audit/criteria artifact.

## Accepted authority to preserve

PL-0135 through PL-0149 are already independently accepted. Preserve them.

In particular:
- one QApplication / Studio shell;
- central navigation/workspace/preferences;
- JobManager and existing `packlab_core.subprocess_runner` cancellation authority;
- diagnostics/version services;
- one versioned project layout;
- ProjectManager and atomic state/revision authority;
- append-only logical history authority;
- recovery lifecycle;
- provenance/invalidation/query seams;
- immutable raw evidence and accepted M05 ingest authority.

Do not redesign accepted foundation merely for convenience.

## Execution order

Execute exactly PL-0150 through PL-0157 in this order. For every child:
1. read its frozen prompt and criteria in full;
2. inspect current accepted main;
3. implement only that child's frozen scope;
4. add production-seam tests;
5. run focused validation;
6. run exact full locked suite;
7. run relevant Ruff/mypy/compileall/project/static checks and `git diff --check`;
8. verify protected files, raw evidence, secrets/privacy, generated binaries and dependency/license state;
9. create implementation/evidence commit(s);
10. create a separate child log-only commit;
11. push and verify remote visibility before starting the next child.

### PL-0150
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_LOG_V01.md

### PL-0151
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_LOG_V01.md

### PL-0152
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_LOG_V01.md

### PL-0153
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_LOG_V01.md

### PL-0154
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_LOG_V01.md

### PL-0155
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_LOG_V01.md

### PL-0156
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_LOG_V01.md

### PL-0157
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_LOG_V01.md

## PL-0150 integration gate

Prove one project portability flow using the accepted ProjectManager/layout/history/provenance authority.

Required:
- portable owned project data is recognized;
- missing required external assets are reported;
- external-present assets are reported but not silently copied;
- regenerable cache/derived data is distinguished;
- symlink/path traversal is safe;
- portable output redacts private absolute paths/secrets;
- raw evidence is not mutated.

## PL-0151 decision gate

Before PL-0152, compare at least two viable PySide6-compatible viewport approaches using reproducible local evidence.

Record:
- candidate versions;
- Python 3.12/PySide6 compatibility;
- Windows support;
- headless/offscreen behavior;
- mesh and point-cloud viability;
- representative local performance evidence;
- dependency and license impact;
- GPU/native limitations actually observed;
- selected backend and exact rationale.

Commit a clear selection/decision artifact.

Do not claim native GPU performance if only software/offscreen rendering was exercised.

## PL-0152–PL-0157 viewport gate

All viewport children must use the single abstraction/backend selected by PL-0151.

Prove one coherent path:

selected viewport adapter
→ mesh/point-cloud load
→ orbit/pan/zoom/fit
→ world grid/axes/mm cues
→ selection/visibility
→ wireframe/normals/point-cloud debug
→ screenshot/export preview
→ reproducible large-mesh benchmark
→ deterministic LOD/display-budget strategy

Requirements:
- no source geometry overwrite;
- no M07 reconstruction work;
- no M09 calibrated measurement/accuracy claim;
- no scattered backend-specific coupling;
- repository-safe fixtures;
- offscreen/headless tests where practical.

## Validation policy

For every child, use the frozen child validation plus the master criteria.

The final batch validation must include:
- exact full locked pytest suite;
- relevant Qt offscreen/UI tests;
- Ruff;
- targeted/relevant mypy for all changed modules;
- compileall;
- repository project/static checks;
- `git diff --check`;
- dependency/lock/license review;
- secrets/privacy/signing-material review;
- generated/binary review;
- verification that `TASKS.md` and ChatGPT audit artifacts were untouched.

Known unrelated mypy debt must be reported truthfully if still present. Do not misreport it as a pass, and do not expand this batch into unrelated cleanup unless the changed code caused the errors.

## Stop conditions

Stop and publish truthful evidence if:
- repository safety/authorization fails;
- PL-0151 cannot make a supported technical selection without a genuine owner decision;
- dependency/license policy would be violated;
- a child would require M07/M09/later-milestone implementation;
- accepted raw evidence would need mutation;
- required tests cannot run truthfully;
- benchmark/performance claims would need fabrication;
- protected ChatGPT/TASKS artifacts would need Codex edits.

## Final handoff

After PL-0157, publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_LOG_V01.md

It must index all eight children and include:
- full GitHub prompt/criteria/log links;
- start commit;
- implementation/evidence commit(s);
- log-only commit;
- focused test results;
- full locked suite result;
- static/project checks;
- dependency/license changes;
- PL-0151 selected viewport and decision evidence;
- PL-0157 benchmark/LOD evidence;
- headless/software-rendering/native/GPU limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not edit TASKS.md. Do not self-audit. Do not start M07.
