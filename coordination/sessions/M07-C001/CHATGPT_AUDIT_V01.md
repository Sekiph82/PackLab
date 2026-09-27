# M07-C001 — ChatGPT Independent Milestone Audit V01

Date: 2026-09-27  
Scope: **PL-0158 through PL-0165**  
Builder head audited: `1b256d5c02a3f35abd90367ce6552a99ecb35036`  
Result: **CHANGES_REQUIRED**

## Evidence reviewed

- Master prompt:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md
- Master audit criteria:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Master builder log:
  https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_LOG_V01.md
- Child prompts, criteria and logs:
  https://github.com/Sekiph82/PackLab/tree/main/coordination/sessions/M07-C001
- Engine baseline:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_baseline.py
- Engine probe:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_probe.py
- Studio engine discovery:
  https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/engine_config.py
- Reconstruction contract:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/reconstruction.py
- Reconstruction process evidence:
  https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/reconstruction_process.py
- Reconstruction workspace:
  https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/reconstruction_workspace.py
- Exact upstream COLMAP 3.12.6 CLI source:
  https://github.com/colmap/colmap/blob/3.12.6/src/colmap/exe/colmap.cc
- Exact upstream OpenMVS 2.4.0 DensifyPointCloud CLI source:
  https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/DensifyPointCloud/DensifyPointCloud.cpp
- Official COLMAP 3.12.6 release:
  https://github.com/colmap/colmap/releases/tag/3.12.6
- Official OpenMVS 2.4.0 release:
  https://github.com/cdcseacave/openMVS/releases/tag/v2.4.0

## Upstream baseline verification

The recorded source revisions are correct.

- COLMAP tag `3.12.6` dereferences to commit `4d5b60e19ad268072adaf1267d21fa38a9a828ca`.
- OpenMVS tag `v2.4.0` points to commit `58117204c86bbb11a0b25b26a8987676cf11274d`.
- COLMAP 3.12.6 publishes official Windows CUDA and non-CUDA release archives.
- OpenMVS 2.4.0 publishes official Windows x64 and Windows x64 CUDA release archives.
- The OpenMVS AGPL high-attention boundary is recorded without claiming distribution clearance.

## Child audit results

### PL-0158 — AUDITED_PASS

The exact COLMAP 3.12.6 source/tag/revision, official Windows release route, licensing provenance, external-executable integration assumption and unavailable local binary hash are recorded truthfully. No unsupported redistribution conclusion is made.

### PL-0159 — AUDITED_PASS

The exact OpenMVS 2.4.0 source/tag/revision and official Windows release route are recorded. AGPL-3.0 is explicitly treated as HIGH LICENSE ATTENTION and bundling/distribution remains a later review gate.

### PL-0160 — CHANGES_REQUIRED

The parser logic is suitable for the selected COLMAP identity banner, but the **production probe invocation is incompatible with the actual selected COLMAP 3.12.6 CLI**.

`engine_probe._default_runner()` always invokes:

`<executable> --version`

The exact COLMAP 3.12.6 `colmap.cc` recognizes `help`, `-h` and `--help`, but does not define a `--version` command. Unknown commands log "Command ... not recognized" and return `EXIT_FAILURE`.

Therefore a real, healthy COLMAP 3.12.6 executable would be classified `UNEXECUTABLE` by the current production probe before its version banner can be accepted.

The focused test does not expose this because its injected runner ignores the actual command arguments and simply returns a synthetic zero-exit `COLMAP 3.12.6` banner.

This violates the mandatory capability-probe requirement even though the fixture suite is green.

### PL-0161 — CHANGES_REQUIRED

The same shared production runner invokes OpenMVS applications with `--version`.

In the exact OpenMVS 2.4.0 DensifyPointCloud CLI, the generic options include `help,h`, but no `version` option. Unknown options are rejected by Boost program_options and initialization returns false. Even the documented help/no-input route prints build/version information and then exits non-zero because no input scene is supplied.

Therefore the current rule "any non-zero probe exit is UNEXECUTABLE" cannot correctly validate the selected OpenMVS applications.

Additionally, the selected pipeline discovers five required OpenMVS components:
- InterfaceCOLMAP
- DensifyPointCloud
- ReconstructMesh
- RefineMesh
- TextureMesh

The current focused probe coverage proves only one generic DensifyPointCloud-style fixture. R01 must prove a deterministic component-suite probe/report so each required executable can be missing/invalid/unsupported/valid independently rather than assuming one executable proves the entire OpenMVS installation.

### PL-0162 — AUDITED_PASS

Discovery is explicit-path-first, supports explicit environment configuration, falls back only to known command names on PATH, reports missing/invalid paths, and does not download/install binaries.

### PL-0163 — AUDITED_PASS

A PackLab-owned backend-neutral protocol, normalized job/input/output records, camera-prior assessment, backend provenance and scale authority are present. M07 manifests explicitly reject `METRIC_VERIFIED`, preserving M09 authority. Portable asset IDs reject absolute paths.

The current enum contains the V1 COLMAP/OpenMVS backend only, which is acceptable at this stage because the protocol boundary, rather than a neural implementation, is the authorized future seam.

### PL-0164 — AUDITED_PASS

Per-stage process evidence reuses the accepted subprocess runner, bounds output, redacts portable evidence, retains timing/exit/cancel/failure state and does not create a second process authority.

### PL-0165 — AUDITED_PASS

Reconstruction workspaces are isolated by reconstruction revision, require an intact RAW_CAPTURE digest, use project-relative paths and atomic writes, integrate successful output with existing provenance, preserve prior completed revisions and reject writes to terminal failed/cancelled workspaces.

## Validation assessment

Builder evidence reports:

- exact full locked suite: `316 passed, 5 skipped, 1 deselected`;
- Ruff: pass;
- targeted mypy: pass;
- compileall: pass;
- `git diff --check`: pass;
- no dependency/lock changes;
- no protected TASKS/audit changes;
- no model/engine binary installation.

Those results are accepted as builder evidence, but the PL-0160/PL-0161 tests are not sensitive to the actual selected CLI invocation semantics. Green fixture tests therefore do not close those two production seams.

The known 18 repository-wide mypy errors remain in five unchanged files and are not a blocker for this remediation.

## Required remediation

1. Replace the shared hard-coded `--version` invocation with **engine-specific probe invocation semantics** grounded in the selected upstream versions.
2. COLMAP 3.12.6 must use a supported non-destructive command such as `help` / `--help`, require the expected successful exit behavior and parse the real version banner.
3. OpenMVS 2.4.0 must use a supported help/no-input probe and explicitly model the selected CLI's expected non-zero help/no-input exit semantics. A recognized version banner under the documented probe mode may be valid even when the known application returns its expected no-input status; arbitrary non-zero failures without a valid banner must remain unexecutable/invalid.
4. Do not weaken execution validation globally just to make OpenMVS pass. The accepted exit behavior must be **probe-policy specific** and tested.
5. Add command-sensitive test runners that assert the exact argv used. A fixture that ignores argv is insufficient.
6. Add OpenMVS component-suite capability reporting/tests for InterfaceCOLMAP, DensifyPointCloud, ReconstructMesh, RefineMesh and TextureMesh, including one missing component and one unsupported-version component.
7. Preserve PL-0158/PL-0159 and PL-0162–PL-0165 behavior and all M06 authority.
8. Re-run focused tests, exact full locked suite, Ruff, targeted mypy, compileall and diff checks.
9. Do not start PL-0166 until independent R01 re-audit returns AUDITED_PASS.

## State

Accepted:
**PL-0158, PL-0159, PL-0162, PL-0163, PL-0164, PL-0165**

Open:
**PL-0160, PL-0161**

M07-C001 remains open.

**CHANGES_REQUIRED**
