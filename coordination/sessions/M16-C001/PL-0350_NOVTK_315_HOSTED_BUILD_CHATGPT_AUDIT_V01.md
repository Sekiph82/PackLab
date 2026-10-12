# PL-0350 — ChatGPT Independent Audit: Host-Gated 315-Module Build Attempt V01

Date: 2026-10-12
Independent verdict: **AUDITED_PARTIAL_CHANGES_REQUIRED**
State: **BATCH_STOPPED_AT_PL-0350 / CAPACITY_PREFLIGHT_SETUP_PYTHON_VERSION_UNAVAILABLE**
PL-0350: **NOT COMPLETE; NO NATIVE BINARY OR INSTALLER**

## Independently inspected evidence

- Host build implementation: https://github.com/Sekiph82/PackLab/commit/ca167dda2fe5c11de3f45e0285fe80b573194c48
- Auto-trigger safety gate: https://github.com/Sekiph82/PackLab/commit/ef2b43bedcec9862653895c630fa23730a83f2d2
- Evidence-only log commit: https://github.com/Sekiph82/PackLab/commit/f996df45
- Published builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Builder blocker report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_REPORT.md
- Master handoff: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Hosted production run: https://github.com/Sekiph82/PackLab/actions/runs/38240655846
- Windows Quality PASS: https://github.com/Sekiph82/PackLab/actions/runs/38240270762
- Actual hosted failed preflight job ID **114782149441**: https://github.com/Sekiph82/PackLab/actions/runs/38240655846/job/114782149441
- Current workflow: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml
- Official setup-python toolcache availability: https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json
- Exact conda Win64 source-build lock: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/packlab-ocp-bindings-win.lock

Auditor fetched the actual Actions job table, **full failed-job logs**, current workflow, current source-build contract, relevant native builder, conda lock and implementation/evidence commit diffs. The job table has capacity-preflight `failure`; jobs `occt-sdk`, `controlled-ocp-runtime` and `build-studio` **skipped**. Quality job `success`. The implementation/evidence commits and narrow runner error match the builder report.

## Root cause verified, not a compiler fault

GitHub-hosted runner is **Windows Server 2022**, started 2026-10-12 11:07:46 UTC. `actions/setup-python` was called with `python-version: 3.12.15`. Exact error:

`The version '3.12.15' with architecture 'x64' was not found for Windows 2022.`

The auditor independently queried the official `actions/python-versions` JSON manifest:
- `3.12.15`, `3.12.14`, `3.12.13`, `3.12.12`: **no win32 x64 setup-python files**.
- `3.12.10`: an official **win32 x64** setup-python distribution exists and the Windows runner image/earlier OwnerDev already uses 3.12.10.
- The PackLab **conda-forge native environment lock** separately pins **Python 3.12.15 win-64** with SHA-256-pinned exact conda package `python-3.12.15-hb12b558_1_cpython.conda` (SHA256 `9476db87d6af903245b160190de22448b07fced7f700b84744858f4df90b5b28`) and `libpython-3.12.15-hcc31f7b_1_cpython.conda` (SHA256 `8a6489422d213c1ce80f156c7d4951b1276b82f09ae329f624969ef93833639c`).

**Important distinction:** The missing `actions/setup-python` Windows binary does NOT prove that the pinned **conda-forge Windows Python 3.12.15** native compiler/interpreter is unavailable. `actions/setup-python` is only a bootstrap for workflow support scripts and needs a Windows-distributed interpreter. The actual controlled OCP build invokes `micromamba run -n packlab-ocp-bindings python`, which must remain the checked-in 3.12.15 conda runtime. No reason to mutate native/source/build contract to 3.12.10.

Exactly **three** `actions/setup-python` occurrences specify `3.12.15` in `windows-studio-build.yml` (preflight, occt-sdk, controlled-ocp-runtime). The packager's separate `python-version: "3.12"` is valid and should remain unchanged.

## Gate-by-gate audit

**A01 PASS:** first safety-only implementation gate made the expensive native build workflow manual-only, required `run_native_build=true`, an exact `main` revision match, and kept normal Python Quality CI. Diff of `ef2b43b` and actual quality/cold run history supports this.

**A02 PASS (implementation/static verification only):** staged OCCT-SDK, official 319→315 no-VTK source preparation, OCP C++ build and production packaging jobs are present in workflow. Prior independently accepted static report and fresh builder evidence show real-archive patched C++/CMake hashes and 315 registration counts, but the auditor did not independently execute real-archive rewrite or a compiler. No native build correctness is certified by source appearance.

**A03 PASS (builder-reported local test + confirmed hosted quality):** full monitored suite 2,061 PASS / 11 SKIP / 1 deselected / 2 warnings; disposable peak ~59MB, left ~15KB; Ruff/format/mypy/compileall passed per builder; exact implementation head SHA quality run independently confirmed SUCCESS. Tests do not establish the installer is portable.

**A04 PASS (safe stop):** capacity preflight failed before actual size measurement or source-patch on runner; three heavy native/package jobs skipped. No cold OCCT/OCP stage, no native cache/checkpoint, no final source/notice/compliance report, no installer and no warm HIT. No repeated run attempted, OwnerDev preserved, root TASKS/audit files not edited by Codex.

**A05 CHANGES REQUIRED (preflight bootstrapping):** all three incompatible setup-python Windows pins must be replaced by a separately pinned, actually available **bootstrap** interpreter, while real native interpreter remains 3.12.15 conda. Add explicit two-interpreter identity assertions so wrong Python is never used to produce or label the OCP extension. Do **not** rewrite the native 3.12.15 lock/source manifests, degrade OCCT/315-module/notice gates or launch the old pywrap path.

## Approved narrow remediation within SAME PL-0350

- Fix only `actions/setup-python` bootstrap pins for the three Windows jobs to **3.12.10**, which official setup-python manifest contains for win32-x64. Preserve exact, verified `micromamba` native Python **3.12.15** and the current cached source-build lock/hash.
- Tighten preflight tests: verify every workflow stage's bootstrap pin is available for `windows-2022`; assert the native OCCT/OCP producer uses `micromamba run` Python 3.12.15, never bootstrap Python 3.12.10; do not silently change conda/native contract.
- After green lightweight/quality tests, run **one corrected manual diagnostic capacity preflight** (or a guarded first capacity phase with heavy jobs disabled until PASS). Capture actual exact job logs. If preflight PASS and conda stage bootstrap/identity viable, continue one controlled cold hosted native build under the owner's original 2026-10-12 approval, avoiding arbitrary repeated retries. If any new blocker, stop and publish; preserve existing source/checkpoints.
- All expensive tasks hosted, current Desktop/OwnerDev protected, no 5h pywrap regeneration, no opaque PyPI wheel substitution. Original installer and separate CACHE HIT acceptance gates unchanged.

Recommended focused prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CODEX_PROMPT.md
Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CHATGPT_AUDIT_CRITERIA.md

## Decision

`AUDITED_PARTIAL_CHANGES_REQUIRED`: accepted safe implementation and verified quality, but actual PL-0350 native build is blocked by an avoidable **bootstrap Python distribution choice** before OCCT compilation. Reuse existing code. Do not escalate to another arbitrary V08/V17 general rebuild. PL-0351 remains unstarted; PL-0368 deferred, no M17.
