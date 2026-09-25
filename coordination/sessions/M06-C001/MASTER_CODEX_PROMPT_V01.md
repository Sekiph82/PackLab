# M06-BATCH-001 — Master Codex Work Order V01

Milestone: **M06 — PackLab Studio Foundation**
Tasks: **PL-0135 through PL-0157** (23 tasks)
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_LOG_V01.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M06
- Current Sprint: M06-BATCH-001
- Current Task: M06-BATCH-001
- Current Task Status: READY
- Required Actor: CODEX
- M03, M04 and M05 marked complete
- PL-0068 still unchecked / OWNER_REQUIRED
- M07 not started
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M07. Never fabricate or close PL-0068.

## Product outcome

At the end of M06 there must be a real PackLab Studio desktop foundation on Windows:

- one PySide6 application shell;
- stable navigation for Library / Capture Inbox / Reconstruction / Editor / Settings;
- dockable workspace infrastructure;
- persistent UI preferences;
- central jobs/activity/cancellation/shutdown behavior;
- local crash/diagnostic bundles and version/about information;
- one versioned PackLab project lifecycle with raw/working/derived/export separation;
- autosave/history/recovery/invalidation/portability services;
- one measured and documented 3D viewport backend choice;
- mesh/point-cloud display with navigation, grid/axes/mm cues, scene selection/visibility, debug modes, screenshot evidence and initial LOD policy.

M06 is **foundation**, not reconstruction. Do not implement COLMAP/OpenMVS or M07 pipeline work.

## Existing authority to preserve

### M05 ingest/transfer authority

The Studio shell must host/reuse:
- `IngestController`;
- `ImportService`;
- `PackLabReceiver`;
- PackScan validation;
- quarantine;
- immutable raw evidence store;
- ingest index;
- import report.

Do not duplicate these inside widgets.

### Raw evidence immutability

M06 project layout may reference or adopt accepted M05 raw evidence, but:
- raw is immutable-by-policy;
- editable/derived/project state lives separately;
- viewport/LOD/debug/autosave/history never overwrites source evidence.

### Subprocess authority

Use `packlab_core.subprocess_runner` for PackLab-owned process cancellation/shutdown boundaries. Do not introduce a second unsafe kill implementation.

## Dependency gate

PL-0135 may add PySide6 as a runtime dependency.

Requirements:
- Python 3.12 compatible;
- version constraint declared in `pyproject.toml`;
- `uv.lock` updated;
- bootstrap remains reproducible;
- dependency/license register updated if project policy requires it;
- no untracked pip install as project state.

PL-0151 may add the selected viewport dependency only after measured spike evidence. Any selected dependency must be declared/locked and license-compatible.

## Architecture rules

### UI/service separation

Widgets/views:
- render service/domain state;
- emit user intent;
- do not own filesystem authority, receiver authority, raw evidence, jobs or revision logic.

Services/domain:
- are testable without a physical display where practical;
- expose structured results/errors;
- maintain project/revision/raw invariants.

### Qt lifecycle

There is exactly one QApplication owner.

No import-time QApplication creation.

All UI tests must support Qt offscreen/headless mode where possible.

### Project authority

One ProjectManager owns current project lifecycle.

One versioned project layout.

One project UUID and revision authority.

One autosave/history/recovery/provenance chain.

No widget-local shadow copy of canonical project state.

### Viewport authority

PL-0151 must select one backend after a focused measured comparison.

PL-0152 onward must use one PackLab viewport abstraction.

Do not scatter backend-specific API calls throughout the Studio shell.

## Ordered children

Execute exactly these 23 tasks in order:

### 1. PL-0135 — PySide6 application shell

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 2. PL-0136 — Main navigation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0136_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0136_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0136_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 3. PL-0137 — Dockable logical workspace layout

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 4. PL-0138 — Persistent window/workspace preferences

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 5. PL-0139 — Global job/activity panel

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 6. PL-0140 — Cancellation and safe shutdown

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 7. PL-0141 — Crash report/log bundle

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 8. PL-0142 — Version/update information screen

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 9. PL-0143 — PackLab project directory layout

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 10. PL-0144 — New/Open/Close project lifecycle

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 11. PL-0145 — Project metadata and revision identifiers

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 12. PL-0146 — Autosave editable project state

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 13. PL-0147 — Non-destructive operation history

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 14. PL-0148 — Interrupted-processing project recovery

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 15. PL-0149 — Derived-artifact invalidation

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 16. PL-0150 — Project portability check

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 17. PL-0151 — 3D viewport technology performance spike

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 18. PL-0152 — Mesh/point-cloud loading and orbit/pan/zoom

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 19. PL-0153 — World grid, axes and millimetre scale cues

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 20. PL-0154 — Object selection and visibility model

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 21. PL-0155 — Wireframe, normals and point-cloud debug modes

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 22. PL-0156 — Viewport screenshot/export preview

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

### 23. PL-0157 — Large-mesh benchmark and viewport LOD strategy

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CHATGPT_AUDIT_CRITERIA_V01.md  
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_LOG_V01.md

Read the frozen child prompt/criteria, inspect current main including earlier M06 children, implement only this child, add production-seam tests, create one implementation/evidence commit, then publish one separate log-only commit ending `READY_FOR_INDEPENDENT_AUDIT`.

## Integration Gate A after PL-0142 — Studio shell

Prove one coherent desktop shell:

QApplication
→ one MainWindow
→ navigation router
→ stable docks/workspace
→ persisted preferences
→ global JobManager
→ safe cancellation/shutdown
→ crash bundle
→ version/about screen.

Capture Inbox must reuse M05 ingest services.

No GUI-thread indefinite waits.

No M07 processing.

## Integration Gate B after PL-0150 — Project lifecycle

Prove one coherent project flow:

New/Open
→ validated versioned project layout
→ immutable raw authority
→ current ProjectManager
→ metadata/revision
→ editable autosave
→ append-only operation history
→ interrupted-job recovery
→ derived provenance/invalidation
→ portability report
→ safe Close.

Requirements:
- raw evidence never mutates;
- stale writes fail rather than overwrite;
- recovery never promotes partial derived data to authority;
- portable project metadata/history does not leak private absolute paths/secrets.

## Integration Gate C after PL-0157 — Viewport foundation

PL-0151 first:
- compare at least two viable PySide6-compatible approaches;
- run representative local synthetic benchmarks;
- record dependency/licensing/headless/GPU limitations;
- select one backend in a committed decision artifact.

Then prove one coherent viewport:

selected backend adapter
→ mesh/point-cloud load
→ orbit/pan/zoom/fit
→ world grid/axes/mm cues
→ scene object selection/visibility
→ wireframe/normals/point-cloud debug
→ screenshot + metadata
→ deterministic interactive LOD/display budget.

Requirements:
- source geometry is never overwritten;
- no M09 measurement-accuracy claims;
- no fake GPU/performance claims;
- offscreen/software-render limitations are recorded truthfully.

## Testing strategy

For Qt:
- set/use offscreen platform in automated tests where required;
- test service/domain logic independently from widget rendering;
- include at least one production widget/app smoke path per UI task.

For viewport:
- use generated repository-safe fixtures;
- avoid huge committed binary assets;
- generate benchmark geometry deterministically;
- mark genuinely expensive benchmarks separately if policy requires, but keep task-critical correctness tests in the normal locked suite.

## Per-child execution discipline

For every child:
1. read TASKS.md, this master prompt/criteria and child prompt/criteria;
2. verify authorization remains valid;
3. inspect current `main`, including earlier M06 children;
4. implement only the frozen child scope;
5. add behavior-bearing tests at the production-used seam;
6. run focused tests;
7. run the exact full locked suite;
8. run Ruff, mypy where configured/relevant, compileall and project/static checks;
9. run `git diff --check`;
10. verify TASKS.md/ChatGPT audits untouched;
11. review secrets/private data/signing/caches/generated binaries;
12. create one implementation/evidence commit;
13. publish the child log in a separate log-only commit;
14. verify remote visibility before continuing.

## STOP conditions

Stop the batch if:
- authorization/repository safety fails;
- a task requires M07/later-milestone implementation;
- a genuine owner/ADR decision is required beyond PL-0151's planned technical decision;
- protected files would need Codex edits;
- raw evidence would need mutation;
- dependency/license policy would be violated;
- full locked tests cannot run truthfully;
- a GPU/native benchmark claim would need fabrication.

On STOP publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

After all 23:
- M03/M04/M05 accepted behavior remains unregressed;
- PL-0068 remains OWNER_REQUIRED;
- no M07 implementation;
- exact full locked suite exits 0;
- relevant Qt offscreen/UI tests pass;
- Ruff/compileall/mypy/project checks pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/secrets/signing/cache/generated-file review clean;
- every child has a distinct implementation/evidence commit and log-only commit;
- PL-0151 selection artifact matches the backend actually used by PL-0152–PL-0157.

Native GPU/UI claims may be made only if genuinely executed. Offscreen/software rendering is acceptable evidence where frozen criteria permit it, but must be labeled accurately.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local filesystem paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_LOG_V01.md

The master log must index all 23 children with:
- full GitHub prompt/criteria/log links;
- start commit;
- implementation/evidence commit;
- log-only commit;
- focused and full-suite results;
- dependency/license changes;
- viewport decision/benchmark evidence;
- native/GPU/headless limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
