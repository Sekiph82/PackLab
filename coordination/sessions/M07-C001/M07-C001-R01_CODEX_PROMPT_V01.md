# M07-C001-R01 — Codex Remediation Work Order V01

Tasks: **PL-0160, PL-0161**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/CHATGPT_AUDIT_V01.md

R01 audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_CRITERIA_V01.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_PROMPT_V01.md

Required remediation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Authorization gate

Before material work, read:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

It must authorize:
- Current Milestone: M07
- Current Sprint: M07-C001-R01
- Current Task: remediate PL-0160 and PL-0161
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- PL-0158, PL-0159 and PL-0162 through PL-0165 already accepted
- PL-0166 not started
- PL-0068 still OWNER_REQUIRED

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- inspect `git status --porcelain`
- inspect `git rev-list --left-right --count HEAD...origin/main`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or discard owner work.

Do not edit root `TASKS.md` or any ChatGPT audit/criteria artifact.

## Root cause to fix

The current production probe in:
https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/engine_probe.py

uses one shared runner that executes:

`<engine> --version`

That is not compatible with the selected real CLIs.

Exact upstream evidence:

COLMAP 3.12.6:
https://github.com/colmap/colmap/blob/3.12.6/src/colmap/exe/colmap.cc

OpenMVS 2.4.0:
https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/DensifyPointCloud/DensifyPointCloud.cpp

COLMAP 3.12.6 supports `help`, `-h`, `--help`; `--version` is treated as an unknown command and exits failure.

OpenMVS 2.4.0 generic options support `help,h`; there is no `--version`. Help/no-input prints the application build/version banner but the application returns failure because no input scene was supplied.

Fixture tests previously hid this because their injected runner ignored the real argv.

## Required design

Refactor probe execution so invocation and accepted exit semantics are explicit and engine-specific.

A suitable architecture is:

```text
EngineProbePolicy
  argv/executable invocation
  accepted probe exit codes
  version parser
  supported baseline versions
```

or an equivalent design with the same properties.

Do not weaken all probes globally.

### COLMAP

Use an actual supported non-destructive command such as:

`colmap help`

or an equivalent upstream-supported help invocation.

Requirements:
- require the expected successful exit;
- parse the version banner from real help output;
- unsupported parseable version -> UNSUPPORTED;
- missing executable -> MISSING;
- failed launch -> UNEXECUTABLE;
- successful but unparseable identity -> INVALID.

### OpenMVS

Use one supported help/no-input mode for the selected application binaries, such as `-h`, grounded in the exact v2.4.0 behavior.

Requirements:
- model the expected OpenMVS help/no-input non-zero exit explicitly;
- valid result requires a recognized version banner plus an allowed probe exit;
- a generic crash/non-zero without the valid banner remains UNEXECUTABLE or INVALID as appropriate;
- do not interpret arbitrary exit code 1 as success outside this probe policy.

## OpenMVS component suite

The selected pipeline requires these components:

- InterfaceCOLMAP
- DensifyPointCloud
- ReconstructMesh
- RefineMesh
- TextureMesh

Add a PackLab-owned aggregate capability report that applies the same version/probe policy to each required component and reports each component separately.

Do not make Studio UI state the authority. If a core-level component descriptor/report is appropriate, keep it in PackLab core and let Studio discovery feed paths into it.

Required test states:
1. all five valid;
2. one missing;
3. one unsupported version;
4. one invalid/unexecutable;
5. aggregate readiness false whenever a required component is not valid.

## Tests

Replace/extend synthetic runners so they receive and assert the exact command/argv.

Mandatory semantic fixtures:

COLMAP:
- runner asserts the selected help invocation;
- returns a realistic 3.12.6 help banner with zero exit.

OpenMVS:
- runner asserts the selected supported help/no-input invocation;
- returns a realistic `OpenMVS x64 v2.4.0` banner with the expected upstream help/no-input exit.

Also prove:
- wrong argv would fail the test;
- OpenMVS expected non-zero + valid banner can be VALID under its specific policy;
- same non-zero without banner is not VALID;
- unsupported version remains UNSUPPORTED;
- missing and launch failure remain distinct.

## Preserve

Do not change the selected baseline versions or source revisions.

Preserve accepted:
- PL-0158
- PL-0159
- PL-0162
- PL-0163
- PL-0164
- PL-0165
- all M06 authorities
- OpenReality-derived backend/geometry authority architecture

Do not install engine binaries.
Do not install OpenReality, VGGT, SAM 3D Objects or TRELLIS.
Do not start PL-0166.

## Validation

Run:
- focused engine-probe tests;
- any engine-config integration tests affected;
- exact full locked suite;
- Ruff;
- targeted mypy for all changed modules;
- compileall;
- project/static checks;
- `git diff --check`;
- protected-file review;
- dependency/lock/license review;
- privacy/secrets/signing/generated/binary review.

Known unrelated repository-wide mypy debt may remain only if unchanged and reported truthfully.

## Publication

Create reviewable remediation implementation/evidence commit(s).

Then publish a separate log-only commit containing:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CODEX_LOG_V01.md

The log must include:
- exact root cause;
- changed files;
- chosen COLMAP probe command;
- chosen OpenMVS probe command/mode;
- explicit accepted exit policies;
- OpenMVS five-component suite results;
- focused and full-suite results;
- static/project checks;
- implementation/evidence commit SHA(s);
- residual limitations;
- full GitHub URLs only.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not edit TASKS.md. Do not self-audit. Do not start PL-0166.
