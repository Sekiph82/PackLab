# PL-0350 - Codex Prompt V07

Task: **Split the controlled OCP/OCCT build from packaging, parallelize pywrap, add verified reusable runtime caching, and finish the unsigned installer**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R08**

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V09.md

V06 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V06.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V07.md

## Start rule

Synchronize the managed checkout non-destructively with latest `origin/main`.

Read:

- live root `TASKS.md`;
- partial audit V09;
- V06 audit;
- current `.github/workflows/windows-studio-build.yml`;
- `tools/packaging/build_controlled_ocp_runtime.py`;
- `tools/packaging/windows_native_source_lock.json`;
- current OCP controlled-runtime manifest validators;
- active OWNER DEV native Desktop EXE policy.

Do not edit root `TASKS.md`.

Preserve the working Desktop `PackLab.exe`; this task is hosted-CI remediation.

## Frozen blocker baseline

Latest quality run:

https://github.com/Sekiph82/PackLab/actions/runs/37860820227

Result: PASS.

Latest production run:

https://github.com/Sekiph82/PackLab/actions/runs/37860820132

Result: canceled during controlled OCP wrapper generation.

Final observed pywrap progress:

- 276 / 319 modules;
- approximately 87%;
- no fatal compiler/bindgen error.

The current OCP source CMake defines `N_PROC=2` by default and invokes bindgen with that value.

## Core V07 architecture

Do not simply raise the same monolithic job timeout again.

Refactor the Windows workflow into two hosted jobs:

### Job 1 — controlled OCP runtime producer

Purpose:

- validate native source/package lock;
- fetch and verify exact corresponding sources;
- build the controlled OCP/OCCT runtime;
- seal it into a deterministic runtime bundle;
- validate the bundle;
- populate reusable cache;
- upload same-run runtime artifact.

### Job 2 — PackLab production packaging

Purpose:

- download the exact same-run controlled runtime artifact from Job 1;
- independently validate it;
- install/overlay it into the locked build environment;
- build PackLab Studio;
- execute existing Qt/PDF/OCP/Open3D smoke;
- execute redistribution inventory/clearance;
- build unsigned installer only after clearance.

Job 2 must never rebuild OCP/OCCT.

## Phase A — explicit controlled-runtime build contract

Extend the controlled runtime build contract to include exact build parameters.

At minimum record:

- source-lock SHA-256;
- OCP source revision;
- pywrap source revision;
- OCCT source revision;
- Python version;
- CMake version;
- compiler ID/version;
- Windows SDK version;
- OCP bindgen worker count;
- CMake/MSBuild parallel count;
- runtime manifest schema version.

Set the OCP CMake cache variable:

`-DN_PROC=4`

and build parallelism:

`--parallel 4`

for the controlled OCP build job.

Do not derive an unbounded worker count from the runner.

The worker count of 4 is part of the auditable build contract.

Add tests proving the workflow/build script explicitly binds `N_PROC=4`.

## Phase B — sealed controlled-runtime bundle

Refactor the builder so it can produce a self-contained controlled runtime bundle without depending on the mutable target environment.

Preferred output layout:

`controlled-ocp-runtime/`

containing at minimum:

- `OCP/` Python package with the built binding and required OCCT DLLs;
- `windows-ocp-controlled-runtime-manifest.json`;
- `windows-native-source-evidence.json`;
- `controlled-runtime-metadata.json`.

Metadata must contain:

- source-lock digest;
- builder-script digest;
- exact source revisions;
- toolchain contract;
- bindgen worker count;
- produced runtime file count;
- every runtime file SHA-256;
- bundle-content digest or canonical manifest digest.

Do not include build trees, compiler intermediates, source archives, secrets or absolute runner paths.

## Phase C — exact reusable cache key

Create a reusable cache key derived only from inputs that can change controlled runtime bytes/authority.

Include at minimum hashes of:

- `tools/packaging/windows_native_source_lock.json`;
- `tools/packaging/packlab-ocp-bindings-win.lock`;
- `tools/packaging/build_controlled_ocp_runtime.py`;
- controlled-runtime validator/installer code;
- workflow build-contract version;
- target OS/arch/Python minor.

Do **not** key the controlled OCP cache on the ordinary PackLab Git commit alone.

Changing unrelated Studio/tests/UI code must not invalidate the native runtime cache.

Do not use broad fallback restore keys that could accept a runtime built from different native inputs.

## Phase D — cache restore must fail closed

A cache hit is only a performance optimization.

After restoring a cached runtime:

1. validate metadata schema;
2. verify exact source-lock digest equals current source lock;
3. verify builder/build-contract digest;
4. verify expected worker/toolchain contract where applicable;
5. hash every runtime file and compare with manifest;
6. prove no unexpected file exists;
7. execute a bounded OCP import/CAD smoke before using the bundle.

If any check fails:

- reject/delete the cache result;
- rebuild from exact sources;
- never silently continue with stale bytes.

## Phase E — same-run artifact transfer

Even when the runtime came from cross-run cache, Job 1 must publish the validated runtime bundle as a same-run short-lived GitHub Actions artifact.

Job 2 must consume that same-run artifact, not directly read a cross-run cache.

Use full-SHA-pinned reviewed upload/download artifact actions.

Record:

- runtime artifact name;
- source-lock digest;
- manifest digest;
- artifact byte size.

## Phase F — package-job controlled-runtime install

Create a deterministic installer/overlay helper if useful, for example:

`tools/packaging/install_controlled_ocp_runtime.py`

It must:

- validate the bundle before install;
- remove the opaque OCP wheel runtime package/libs from the target environment;
- install only the controlled `OCP` package/runtime;
- preserve the manifest for later inventory validation;
- fail if opaque `cadquery_ocp_novtk.libs` survives.

The production PyInstaller build must consume only this controlled runtime.

## Phase G — preserve all existing PL-0350 gates

After controlled runtime installation, keep the existing production sequence:

1. production Studio staging;
2. staged Qt surface assertion;
3. frozen no-network Qt GUI + QtPdf + OCP/CAD + Open3D smoke;
4. bidirectional controlled OCP manifest validation;
5. exact redistribution inventory;
6. pre-clearance evidence;
7. engineering clearance.

Clearance still requires:

- unresolved shipped files = 0;
- unresolved components = 0;
- missing notices = 0;
- missing source packages = 0;
- forbidden Qt components = 0;
- `engineering_packaging_status = CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`;
- `legal_review_required=true`;
- `public_release_authorized=false`.

## Phase H — installer

Only after clearance:

- add reviewed compliance texts;
- re-inventory final installer input;
- rerun frozen capability smoke where required by the existing contract;
- build versioned unsigned Inno installer;
- record exact installer SHA-256/bytes/tool version;
- upload final compliance evidence + required source evidence + unsigned installer.

No tag, GitHub Release, signing claim or V0.1 release.

## Phase I — hosted proof expectations

The first V07 run may be a cache miss.

It must still complete the controlled runtime producer job inside the hosted job limit.

Record timings for:

- source/environment setup;
- OCCT build;
- pywrap generation;
- OCP native compile/link;
- bundle validation/upload;
- packaging job.

The pywrap phase must record start/end and worker count.

If `N_PROC=4` still cannot finish before the hosted limit, stop and report exact progress/timings. Do not increase beyond 4 without a new audit because memory/stability must remain bounded.

Then demonstrate a second hosted run or explicit workflow rerun where the controlled runtime cache is a verified HIT and Job 1 completes without rebuilding pywrap.

The cache-hit proof is mandatory before V07 can be considered complete.

## Phase J — workflow concurrency

Avoid wasting a completed controlled runtime because of unrelated follow-up commits.

The controlled runtime cache/artifact producer must have a stable cache identity independent of normal Studio source changes.

Preserve reasonable workflow concurrency, but do not allow a cache-hit path to be invalidated simply because an unrelated UI/test file changed.

Do not disable all concurrency safeguards globally without justification.

## Phase K — tests

Add focused tests for:

- exact `N_PROC=4` binding;
- exact cache-key inputs;
- no broad fallback cache key;
- cache metadata mismatch rejection;
- runtime-file digest mismatch rejection;
- unexpected runtime-file rejection;
- opaque OCP libs absent after install;
- same-run artifact dependency contract;
- packaging job never invokes the controlled OCP builder;
- cache-hit path still runs validation and OCP smoke.

Run:

- `uv lock --check`;
- Ruff/format;
- mypy;
- focused CI/packaging tests;
- full locked pytest;
- compile checks;
- `git diff --check`;
- privacy/secrets/scope review.

## OWNER DEV standing delivery

After implementation/evidence publication and remote parity, refresh the accepted native Desktop PackLab owner runtime.

Do not regress it to LNK/PowerShell.

## GitHub-link publication contract

All owner-facing handoffs and published logs must use GitHub HTTPS links for:

- implementation commit(s);
- evidence commit(s);
- PL-0350 V07 Codex log;
- R08 master Codex log;
- quality run;
- runtime-producer/build run;
- cache-hit proof run;
- relevant Actions artifacts;
- prompt/criteria.

Do not use local `C:\...` links as handoff references.

## Stop conditions

Stop truthfully if:

- controlled runtime producer exceeds hosted job limit even with `N_PROC=4`;
- cache validation cannot be made fail-closed;
- controlled-runtime smoke fails;
- packaged capability regresses;
- redistribution remains unresolved;
- required source/notice evidence remains missing;
- installer cannot be built after clearance.

Do not start PL-0351 until PL-0350 V07 is green and an unsigned installer exists.

## Handoff

Publish implementation/evidence commit(s), then:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V07.md`

as a distinct log-only commit.

If blocked, end child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`

and stop master at:

`AWAITING_MILESTONE_AUDIT`

If green, continue automatically to PL-0351 under the master continuation.
