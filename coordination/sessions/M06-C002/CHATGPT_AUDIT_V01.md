# M06-C002 — ChatGPT Independent Milestone Audit V01

Date: 2026-09-27  
Scope: **PL-0150 through PL-0157** and integrated M06 continuation  
Remote head audited: `3bbc438a4177f4bbb2dedd8278f62dd09afe4f4d`  
Overall result: **CHANGES_REQUIRED**

## Evidence reviewed

- Master work order:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Master audit criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Master builder log:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_LOG_V01.md
- Frozen child criteria and prompts for PL-0150 through PL-0157:
  https://github.com/Sekiph82/PackLab/tree/main/coordination/sessions/M06-C001
- Production source under:
  https://github.com/Sekiph82/PackLab/tree/main/apps/windows-studio/src/packlab_studio
- Viewport decision/evidence:
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0002-m06-viewport-backend.md
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-spike-v01.json
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/M06_VIEWPORT_PERFORMANCE.md
  https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-benchmark-v01.json
- Tests:
  https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_portability.py
  https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_viewport.py
  https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_viewport_lod.py
  https://github.com/Sekiph82/PackLab/blob/main/tests/studio/test_viewport_spike.py

## Child results

| Task | Result | Audit note |
|---|---|---|
| PL-0150 | CHANGES_REQUIRED | Production scanner contains symlink handling, but the frozen mandatory criteria explicitly require tests for **symlink/path traversal**. The committed portability tests cover traversal strings only; no real symlink escape/in-project symlink test is present. |
| PL-0151 | CHANGES_REQUIRED | The frozen criteria require executable spikes using representative synthetic **point/triangle counts** and measured startup/load/render-or-interaction proxy, memory observations and dependency weight. The current spike measures QPainter point rendering only. The OpenGL candidate is only a context probe, with no synthetic geometry workload, no comparable timing/memory evidence, and no triangle workload. |
| PL-0152 | AUDITED_PASS | One PackLab-owned adapter/service boundary exists; local mesh/point-cloud loading, structured errors, camera orbit/pan/zoom/fit/reset and offscreen rendering are implemented without source mutation. |
| PL-0153 | AUDITED_PASS | Grid/axes/mm state and adaptive spacing metadata are deterministic and explicitly visual-only; no calibrated M09 accuracy claim is made. |
| PL-0154 | AUDITED_PASS | Stable scene object IDs/types, single-selection, visibility, hidden-selection clearing and object-tree snapshot seam are implemented through one scene model. |
| PL-0155 | AUDITED_PASS | Solid/wireframe/normals/point-cloud modes are backend-independent view state; missing normals use temporary derived display normals and do not mutate source geometry. |
| PL-0156 | AUDITED_PASS | PNG preview export and redacted sidecar metadata use the selected adapter, reject raw-area output, require explicit overwrite and atomically publish each output file. |
| PL-0157 | CHANGES_REQUIRED | The task/master criteria call for a **large-mesh/point-cloud** performance benchmark. The committed benchmark executes only synthetic point clouds. Mesh LOD correctness is unit-tested, but no reproducible mesh benchmark/evidence case is recorded. |

## Validation assessment

Builder evidence reports:
- exact locked suite: `291 passed, 4 skipped, 1 deselected`;
- Ruff: pass;
- targeted mypy for changed modules: pass;
- compileall: pass;
- `git diff --check`: pass;
- no protected tracker/audit edits;
- no dependency/lock changes;
- no private scans/secrets/signing material/large binaries.

The repository-wide 18-error mypy debt is explicitly reported as pre-existing and does not involve changed C002 modules. This is not a blocker for the identified remediation scope.

## Mandatory remediation

1. **PL-0150:** add real filesystem symlink coverage, including an escaping symlink classified unsafe and a safe in-project link/path case where the host permits symlink creation. Tests must remain deterministic on Windows; if privilege/policy prevents symlink creation, use a capability-aware skip only for the actual symlink case while keeping traversal coverage mandatory.
2. **PL-0151:** rerun the technology comparison with at least two genuinely executable/meaningfully comparable viewport approaches on the available host. Each compared executable candidate must receive representative synthetic point **and triangle/mesh** workloads where the candidate supports them. Record comparable startup/initialization, geometry load/setup, render/interaction proxy, memory observation, dependency footprint/weight, licensing, headless/native capability and limitations.
3. If the existing Qt OpenGL candidate cannot execute a geometry workload on the host, do not fabricate metrics. Replace or supplement it with a second actually executable PySide6-compatible candidate suitable for the M06 decision, and update the ADR/evidence truthfully.
4. **PL-0157:** extend the reproducible benchmark and committed evidence with representative synthetic mesh cases at multiple sizes in addition to point clouds. Record source/display primitive counts, LOD behavior, initialization/display/render proxy and memory observation. Keep source geometry immutable.
5. Re-run the focused suites and exact full locked suite plus Ruff, targeted mypy, compileall and diff/project checks.
6. Preserve accepted PL-0152 through PL-0156 behavior, accepted PL-0135 through PL-0149, M03–M05, PL-0068 OWNER_REQUIRED and the M07 boundary.
7. Do not start M07 until independent R02 re-audit returns `AUDITED_PASS`.

## State

Accepted in this audit:
**PL-0152, PL-0153, PL-0154, PL-0155, PL-0156**

Open:
**PL-0150, PL-0151, PL-0157**

M06 remains open.

**CHANGES_REQUIRED**
