# M06-R02 — Codex Remediation Work Order V01

Tasks: **PL-0150, PL-0151, PL-0157**

Repository:
https://github.com/Sekiph82/PackLab

Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/CHATGPT_AUDIT_V01.md

R02 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CHATGPT_AUDIT_CRITERIA_V01.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CODEX_PROMPT_V01.md

Required R02 log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CODEX_LOG_V01.md

Prior master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_LOG_V01.md

## Authorization gate

Before material work, read:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

It must authorize:
- Current Milestone: M06
- Current Sprint: M06-R02
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- remediation scope exactly PL-0150, PL-0151 and PL-0157
- PL-0152 through PL-0156 already accepted
- PL-0135 through PL-0149 already accepted
- PL-0068 still OWNER_REQUIRED
- M07 not started

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git status --porcelain`
- `git rev-list --left-right --count HEAD...origin/main`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or discard owner work.

Never edit:
- https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/CHATGPT_AUDIT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CHATGPT_AUDIT_CRITERIA_V01.md
- any other ChatGPT audit/criteria artifact.

Do not start M07.

## Read before editing

Read in full:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/CHATGPT_AUDIT_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CHATGPT_AUDIT_CRITERIA_V01.md

Re-read the frozen criteria:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CHATGPT_AUDIT_CRITERIA_V01.md

## PL-0150 remediation

Keep the existing production scanner and read-only behavior unless a real defect is found.

Add real filesystem symlink coverage in:
https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_portability.py

Mandatory scenarios:
1. symlink inside the project that resolves outside the project root -> `UNSAFE_LINK`;
2. safe project-owned reference/link behavior remains portable;
3. existing traversal-string coverage remains;
4. report remains redacted and no source/raw/external file is copied or modified.

On Windows, create the symlink for the test only when the host permits it. If Windows policy/developer mode/privilege blocks symlink creation, skip only that actual-symlink case with an explicit capability reason. Do not silently replace it with another traversal-string test.

## PL-0151 remediation

The existing spike is insufficient because it benchmarks only point rendering for the selected raster candidate and treats the OpenGL candidate as a context probe.

Update:
https://github.com/Sekiph82/PackLab/blob/main/tools/viewport_spike.py

https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_viewport_spike.py

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-spike-v01.json

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0002-m06-viewport-backend.md

Requirements:

1. Compare at least two genuinely executable or meaningfully testable PySide6-compatible viewport approaches on the available host.
2. Every candidate that can execute a rendering workload must receive both:
   - synthetic point-cloud workloads;
   - synthetic triangle/mesh workloads.
3. Record comparable:
   - startup/initialization time;
   - geometry setup/load time;
   - render or interaction proxy time;
   - memory observation/proxy;
   - dependency footprint/weight;
   - licensing;
   - Python 3.12 / PySide6 / Windows compatibility;
   - headless capability;
   - native/GPU capability and limitations.
4. Keep unavailable OpenGL/native paths truthful. If the existing Qt OpenGL path cannot run a geometry workload, it may remain as a capability probe, but it does **not** satisfy the measured second-candidate requirement by itself.
5. Add or use a second actually executable candidate when needed. Prefer a dependency-free PySide6 option if technically credible, for example a separate Qt item/scene-based software projection path versus the existing immediate QImage/QPainter path. Do not call two thin wrappers around the exact same execution path independent candidates.
6. Do not add a heavy third-party dependency solely to manufacture a comparison unless the dependency/license/lock impact is justified and recorded.
7. Update the ADR so the selected backend decision follows the new evidence.
8. Do not change PL-0152–PL-0156 public behavior unless required to keep the selected adapter decision consistent.

## PL-0157 remediation

Extend:

https://github.com/Sekiph82/PackLab/blob/main/tools/viewport_benchmark.py

https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_viewport_lod.py

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-benchmark-v01.json

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/M06_VIEWPORT_PERFORMANCE.md

Mandatory:
1. retain point-cloud benchmark cases;
2. add synthetic mesh/triangle benchmark cases at multiple representative sizes;
3. record for each case:
   - geometry type;
   - source primitive count;
   - display primitive count;
   - LOD plan/stride/budget;
   - initialization/setup time;
   - display-representation time;
   - render/interaction proxy time;
   - memory observation;
   - image/output proxy where applicable;
4. use the selected PL-0151 backend;
5. never mutate source geometry;
6. do not claim native GPU throughput if it was not measured.

Make benchmark schema tests assert both point-cloud and mesh evidence exist.

## Regression boundary

Preserve:
- PL-0135 through PL-0149 accepted behavior;
- PL-0152 through PL-0156 accepted behavior;
- M03–M05 accepted behavior;
- immutable raw authority;
- ProjectManager/recovery/provenance authority;
- viewport service/adapter abstraction;
- PL-0068 OWNER_REQUIRED;
- M07 not started.

## Validation

Run focused tests for PL-0150, PL-0151 and PL-0157, then the exact full locked suite.

Also run:
- Ruff;
- targeted/relevant mypy for all changed modules;
- compileall;
- repository project/static checks;
- `git diff --check`;
- protected-file review;
- dependency/lock/license review;
- secrets/privacy/signing/generated/binary review.

Known unrelated repository-wide mypy debt may remain only if unchanged and explicitly reported.

## Commit and handoff

Create reviewable implementation/evidence commit(s), then a separate log-only commit containing:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CODEX_LOG_V01.md

The log must contain:
- exact remediation result for PL-0150, PL-0151 and PL-0157;
- changed files;
- spike candidate definitions and actual measured workloads;
- updated viewport selection result;
- point-cloud and mesh benchmark evidence summary;
- focused tests;
- exact full-suite result;
- static/project checks;
- implementation/evidence commit SHAs;
- log-only commit SHA when available;
- residual limitations;
- full GitHub URLs only.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not edit TASKS.md. Do not self-audit. Do not start M07.
