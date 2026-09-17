# PL-0005-C001 — Codex Prompt V01

Status: **ISSUED**

Task: **PL-0005 — Create dependency/license register for NextLevel, COLMAP, OpenMVS, Open3D, OpenCV, PyTorch, OpenCascade bindings, Blender and PySide6.**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Mandatory inputs

Read before material implementation:

1. root `AGENTS.md`
2. root `TASKS.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `docs/architecture/REPOSITORY_STRUCTURE.md`
5. `docs/architecture/GLOSSARY.md`
6. `docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md`
7. `docs/architecture/adr/README.md`
8. `docs/architecture/adr/ADR-0001-monorepo-architecture.md`
9. `coordination/README.md`
10. `coordination/AUDIT_POLICY.md`
11. `coordination/AUDIT_INDEX.md`
12. `coordination/sessions/PL-0004-C001/CHATGPT_AUDIT_V01.md`
13. this prompt
14. `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

If root `TASKS.md` does not declare PL-0005 as the current authorized task for Codex, STOP and report `TASK_STATE_MISMATCH`.

## Phase 0 — Safe synchronization

Use normal post-bootstrap synchronization only.

Run:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- verify Git root and `origin` identify `Sekiph82/PackLab`;
- historical untracked `.hiveai/` state may remain local but must not be staged or treated as project truth;
- if tracked state is clean and local is only behind, use `git merge --ff-only origin/main`;
- if local is ahead, diverged, or has unexpected tracked changes, STOP and report exact state;
- do not reset, rebase, force-push, destructive checkout, silent stash, or `git clean`;
- before implementation prove local HEAD equals `origin/main` and TASKS.md authorizes PL-0005.

## Phase 1 — Research authoritative dependency/license evidence

Create a dependency/license register from authoritative upstream sources. Do not infer licenses from blog posts, package aggregators, random mirrors, search snippets, or memory when an upstream LICENSE/COPYRIGHT/project documentation source exists.

Research at minimum these PackLab dependencies/capabilities:

1. NextLevel
2. COLMAP
3. OpenMVS
4. Open3D
5. OpenCV
6. PyTorch
7. Open CASCADE Technology (OCCT)
8. the Python OpenCascade binding layer, which is **not yet selected**
9. Blender
10. PySide6 / Qt for Python

Although the permanent task title says “OpenCascade bindings,” PL-0005 must not pretend that a specific Python binding has already been selected. PL-0289 later performs the binding selection. Record OCCT itself separately from candidate Python binding licensing and mark the final binding as `TBD / not selected` unless an already-audited PackLab decision says otherwise.

### Required authoritative source expectations

Use current upstream evidence where available, including these canonical families:

- NextLevel: `https://github.com/NextLevel/NextLevel` and its LICENSE.
- COLMAP: `https://colmap.github.io/license.html` and/or canonical `colmap/colmap` repository license evidence.
- OpenMVS: `https://github.com/cdcseacave/openMVS` LICENSE/COPYRIGHT.
- Open3D: `https://www.open3d.org/` and canonical repository LICENSE.
- OpenCV: `https://opencv.org/license/` and canonical repository license evidence.
- PyTorch: canonical `pytorch/pytorch` LICENSE/NOTICE/packaging metadata as needed.
- OCCT: `https://github.com/Open-Cascade-SAS/OCCT` license files and special exception.
- Blender: `https://www.blender.org/about/license/`.
- PySide6 / Qt for Python: `https://doc.qt.io/qtforpython-6/` and relevant Qt licensing pages.

For the not-yet-selected Python OpenCascade binding, research candidate evidence only if useful. Do not convert a candidate into a PackLab selection in this task.

## Phase 2 — Create the dependency/license register

Create exactly:

`docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

The register is a governance/compliance record, **not legal advice** and not a final distribution approval.

### Required header / scope

State:

- evidence/review date;
- PackLab is currently a personal-use project, but public repository and future binary/source distribution scenarios require license discipline;
- license facts can change by version/component/build configuration;
- transitive/optional third-party dependencies must be reviewed when versions/builds are pinned;
- PL-0005 does not install, pin, vendor, bundle, link, or distribute any dependency;
- exact compatibility/version selection belongs to later tasks.

### Required register fields

For each named dependency/capability include at least:

- Dependency / capability
- PackLab role
- Planned integration mode
- Current selection status
- Upstream project / canonical source
- Primary license(s)
- License evidence URL(s)
- Important third-party/transitive caveat
- PackLab compliance/distribution note
- Version/pin status
- Follow-up task(s)
- Risk/attention classification

Use a readable table plus focused notes where a single table cell would become misleading.

### Mandatory factual/license distinctions

The register must reflect current authoritative evidence without overclaiming:

#### NextLevel

- canonical upstream is `NextLevel/NextLevel`;
- upstream LICENSE is MIT;
- intended PackLab role is iOS camera-control abstraction behind PackLab-owned interfaces;
- exact version pin remains later work (PL-0037);
- dependency/transitive Swift package contents must still be reviewed when pinned.

#### COLMAP

- COLMAP itself is licensed under the new BSD / 3-clause BSD terms shown by its official license page;
- its own license page explicitly says third-party dependencies are separately licensed and can affect a resulting build/distribution;
- PackLab role is SfM/sparse reconstruction behind an adapter;
- planned integration should remain an external-engine boundary unless later audited architecture changes it;
- do not claim that the core COLMAP license alone clears every binary build for redistribution.

#### OpenMVS

- canonical upstream is `cdcseacave/openMVS`;
- repository license is GNU AGPL v3;
- PackLab role is dense cloud / mesh / refinement / texturing behind an external-engine adapter;
- mark OpenMVS as **HIGH LICENSE ATTENTION** for any future distribution, bundling, modification, linking, service/network exposure, or closed-source commercialization scenario;
- do not make a legal conclusion that a particular future PackLab distribution model is automatically compliant or non-compliant;
- require explicit license review before PackLab distributes/bundles OpenMVS or materially changes the integration model.

#### Open3D

- upstream states MIT license;
- PackLab role is point-cloud/mesh analysis, cleanup, registration, measurement/deviation support;
- still record third-party dependency/build caveats and later version pin.

#### OpenCV

- official OpenCV licensing page states OpenCV 4.5.0 and higher use Apache License 2.0, while 4.4.0 and lower use 3-clause BSD;
- because PackLab has not pinned the version yet, record this version-sensitive distinction rather than asserting one license for every OpenCV version;
- later pinned version must drive the final compliance record.

#### PyTorch

- record the main PyTorch project's BSD-3-Clause licensing evidence;
- also record that installed/package/source distributions include third-party components with their own licenses and that packaging metadata may express multiple component licenses;
- do not simplify the entire installed dependency graph to a single BSD sentence;
- later pinned package/build needs a dependency/NOTICE review.

#### Open CASCADE Technology (OCCT)

- OCCT itself is under LGPL 2.1 with the Open CASCADE special exception, with alternative commercial terms available;
- reference the actual OCCT license and exception evidence;
- PackLab role is engineering BREP/CAD/STEP capability;
- separate OCCT licensing from Python binding licensing.

#### Python OpenCascade binding layer

- final binding is `TBD / not selected` in PL-0005;
- PL-0289 remains the selection/compatibility task;
- candidate bindings may have licenses different from OCCT itself;
- do not state that every OpenCascade Python binding inherits OCCT's LGPL-2.1+exception license;
- if `pythonocc-core` is mentioned as a candidate, identify it only as a candidate and source its own license evidence separately.

#### Blender

- Blender's official license page states Blender is GPL and explains that distributed Blender binaries are under GPL-compatible terms;
- Blender's page also distinguishes user-created artwork/output from Blender software licensing;
- PackLab role is headless/external render, UV/material/presentation automation, not dimensional truth;
- flag published/distributed Blender Python scripts/add-ons for GPL compatibility review based on Blender's own guidance;
- do not claim that rendered images or ordinary user output automatically become GPL.

#### PySide6 / Qt for Python

- official Qt for Python documentation says PySide6/Qt for Python is available under LGPLv3/GPLv3 and the Qt commercial license;
- note Qt/module/third-party licensing can vary and must be checked for the modules actually shipped;
- PackLab role is Windows desktop presentation;
- final packaging/distribution must comply with the selected Qt/PySide licensing route and notices/relocation/relinking obligations as applicable;
- do not give legal advice or declare proprietary distribution automatically cleared.

### Risk / attention classification

Define at least:

- LOW ATTENTION — permissive primary license, still requires notices/transitive review.
- MEDIUM ATTENTION — license/version/build/module choices materially affect obligations.
- HIGH LICENSE ATTENTION — strong copyleft or architecture/distribution choices require explicit review before distribution.
- TBD / NOT SELECTED — component choice itself is not yet frozen.

The classification is project governance triage, not a legal opinion.

At minimum:

- OpenMVS must be HIGH LICENSE ATTENTION.
- Python OpenCascade binding must be TBD / NOT SELECTED until PL-0289.
- version-sensitive OpenCV licensing must not be flattened.
- PySide6/Qt must not be treated as a single unconditional permissive license.

### Integration architecture notes

Preserve accepted PackLab architecture:

- external engines remain behind PackLab-owned adapters/capability boundaries;
- CLI/external-process use does not by itself prove a particular legal conclusion, but the integration mode must be recorded because it is relevant to later review;
- NextLevel remains behind PackLab-owned capture interfaces;
- PySide6 UI does not own domain truth;
- Blender does not own dimensional truth;
- license register does not change Scan Master/Design Model ownership.

### Distribution scenarios

Include a short matrix for at least:

1. personal/local use only;
2. public source repository;
3. distributing a PackLab Windows installer/binary;
4. bundling third-party binaries with PackLab;
5. modifying third-party source;
6. offering a network/service deployment where AGPL software might be involved.

For each scenario state what must be re-reviewed. Do not issue legal conclusions beyond clearly stated upstream license facts. Use language such as `requires compliance review before release` where appropriate.

### Compliance checklist

Include a future-release checklist covering at least:

- pin exact version/commit;
- save upstream license/NOTICE evidence for that version;
- inventory transitive dependencies actually shipped;
- record whether dependency is linked, invoked as external executable, bundled, modified, or downloaded separately;
- preserve required copyright/license notices;
- verify source-offer/source-availability obligations for copyleft components when applicable;
- check PySide6/Qt modules actually shipped;
- check Blender scripts/add-ons if distributed;
- review OpenMVS integration/distribution explicitly;
- review chosen OpenCascade Python binding separately from OCCT;
- do not treat this register as legal counsel.

## Scope boundaries

Authorized changes:

- add `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`;
- add matching `coordination/sessions/PL-0005-C001/CODEX_LOG_V01.md`.

Do not modify:

- root `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- existing architecture baseline/structure/glossary/ADR files;
- coordination policy/index;
- prior session evidence;
- this prompt or criteria;
- root `AUDIT.md` or `handoff.md`;
- application/source/schema/runtime files.

Do not install dependencies and do not implement PL-0006+.

## Validation

Run and record:

```powershell
git diff --check
```

For the new file, use a diff that can see an untracked file:

```powershell
git add -N docs/architecture/DEPENDENCY_LICENSE_REGISTER.md
git diff -- docs/architecture/DEPENDENCY_LICENSE_REGISTER.md
```

Perform explicit checks proving:

- every required dependency/capability is present;
- every license claim has a canonical/authoritative source;
- OpenMVS is AGPL-3.0 and HIGH LICENSE ATTENTION;
- COLMAP third-party dependency caveat is present;
- OpenCV license is version-sensitive around 4.5.0;
- PyTorch third-party/package-license caveat is present;
- OCCT and Python binding licenses are separated;
- binding remains TBD/not selected;
- Blender software vs output distinction is present;
- PySide6/Qt licensing is multi-route/module-sensitive;
- no dependency is falsely claimed installed/pinned/redistribution-cleared;
- no legal-advice conclusion is presented as fact;
- no protected files are modified;
- no PL-0006+ work is added.

No application test suite is required for this documentation/governance task.

## Required Codex log

Write:

`coordination/sessions/PL-0005-C001/CODEX_LOG_V01.md`

Record:

- prompt/criteria paths;
- synchronized starting commit;
- implementation commit;
- synchronization commands/results;
- inputs read;
- authoritative license/source URLs consulted;
- files added/modified/deleted;
- implementation summary;
- exact validation commands, expected results, failure conditions and actual results;
- new-file diff-review evidence;
- any conflicting/ambiguous upstream licensing evidence and how it was represented without guessing;
- privacy/security check;
- scope check;
- push/remote visibility evidence;
- known limitations/unverified legal interpretations;
- final `AWAITING_AUDIT`.

### Commit-SHA metadata rule

Following AL-PL-0007:

- record `startingCommit` and `implementationCommit`;
- do not predeclare a future log-containing `finalCommit` SHA;
- ChatGPT records the actual audited head after push.

## Commit / push

Commit only the authorized dependency/license register and matching Codex log.

Push safely to `origin/main` and verify remote visibility.

## Final response

Return only a concise handoff containing:

- `PL-0005-C001`;
- implementation commit information;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP. Do not begin PL-0006.
