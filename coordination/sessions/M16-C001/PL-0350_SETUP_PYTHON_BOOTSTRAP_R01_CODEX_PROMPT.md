# PL-0350 — Narrow R01: Windows setup-python Bootstrap Repair, Then Guarded Native Continuation

**Executor: CODEX. Repo: Sekiph82/PackLab, main. SAME PL-0350 task.**
**Use existing owner authorization for hosted source-built 315-module no-VTK OCP/OCCT; this R01 does NOT authorize new architecture, opaque wheel, large local build, or repeated cold retries.**
Parent prompt (do not silently supersede its provenance/installer gates):
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_PROMPT.md
Latest independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CHATGPT_AUDIT_V01.md
Matching R01 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CHATGPT_AUDIT_CRITERIA.md

## Frozen factual diagnosis

Hosted run https://github.com/Sekiph82/PackLab/actions/runs/38240655846 at implementation SHA `ca167dda2fe5c11de3f45e0285fe80b573194c48` **never reached native compilation**. Its Windows-2022 preflight `actions/setup-python` requested `3.12.15`; that version's GitHub setup-python Windows x64 artifact is unavailable. Official manifest https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json lists no Win32-x64 packages for Python 3.12.12–3.12.15, but DOES list `3.12.10-win32-x64`. This is a **bootstrap installer artifact** problem, not proof the actual locked native Python 3.12.15 conda-forge build is missing.

Native conda lock is already exact and must be maintained: `tools/packaging/packlab-ocp-bindings-win.lock` pins `python=3.12.15` win-64 SHA256 `9476db87d6af903245b160190de22448b07fced7f700b84744858f4df90b5b28`, `libpython=3.12.15` SHA256 `8a6489422d213c1ce80f156c7d4951b1276b82f09ae329f624969ef93833639c`; real OCCT/OCP native compilation must use **micromamba's 3.12.15 executable and headers**. Do NOT downgrade the frozen `controlled_ocp_runtime_contract.json` `target.python_version` from 3.12.15, rewrite conda lock/source digest, switch to other Python minor, or weaken byte/provenance checks.

## R01.1 — minimal version fix in existing manual-only workflow

1. Non-destructively sync a clean managed worktree to live origin/main. Read `git show origin/main:TASKS.md`; protect owner's dirty Desktop, previous-good EXE and other projects; do NOT edit root TASKS.md, owner decisions or ChatGPT audits. Confirm `.github/workflows/windows-studio-build.yml` is STILL manual-only with affirmative `run_native_build` and exact-ref gates, and quality workflow stays live.
2. Change exactly **the three** `actions/setup-python` **bootstrap** calls in `capacity-preflight`, `occt-sdk`, `controlled-ocp-runtime` from `3.12.15` to **`3.12.10`**, an explicit available win32-x64 toolcache version. Preserve the package job's present compatible `python-version: "3.12"` or align to `3.12.10` only if necessary for a verified package contract. Do not rewrite every textual 3.12.15; the native 3.12.15 source/build lock and conda setup remain immutable.
3. Update precise tests `tests/ci/test_windows_studio_build_workflow.py` and, if necessary, a tiny regression check to assert **separate** identities: Windows setup-python bootstrap 3.12.10 in these three jobs, actual OCP/OCCT producer `micromamba run -n packlab-ocp-bindings python` 3.12.15; ensure exact OCP compiler Python headers and CMake `Python_EXECUTABLE` are derived from micromamba/native interpreter, not PATH bootstrap. Add explicit hosted `micromamba run -n packlab-ocp-bindings python -c "import sys; assert sys.version_info[:3] == (3,12,15); print(sys.executable)"` before native CMake in both jobs and fail closed if mismatch. Do not accidentally use `uv run`/setup-python interpreter in native compilation.
4. Add an optional explicit `preflight_only` boolean dispatch input (default `false`) that runs ONLY `capacity-preflight`, guaranteeing OCCT/OCP/Studio jobs skip by tested job-level condition when `preflight_only=true`. It must not broaden automatic trigger events. Ensure resulting YAML has guarded affirmative `run_native_build=true`, matching full revision and ref; no implicit native launch in preflight-only mode.
5. The capacity-preflight-only path must record actual hosted runner Python bootstrap identity and available capacity/storage + actual official ZIP no-VTK patch checks. It does not have to install the full native conda environment if budget/runner stage permissions prevent it, but do NOT claim native conda environment is tested until it is actually installed in subsequent job. If useful, a bounded read-only conda package availability/download check may be added before any OCCT compiler invocation; do not preemptively replace exact locks.
6. Tiny YAML/fixture tests must catch attempted regression to unavailable Win32 patch, failure of `preflight_only` to skip all native jobs, exact Python native-vs-bootstrap mismatch, and inadvertent loss of manual-only trigger restriction.

## R01.2 — validate quality; guarded follow-on

- Run short focused tests, relevant static/negative preflight unit tests and no-giant-dir monitored suite under existing local 40GiB-free / 4GiB pytest / 2GiB fixtures / 8GiB total disposable protections. No local OCCT/pywrap/C++ compilation and no owner Desktop EXE modifications. Quality, Ruff, mypy, workflow parsing, `git diff --check`. Avoid unnecessary full-suite rerun if no native Python source change, but disclose actual tests.
- Commit minimal implementation, push to main after verifying workflow is manual-only and no accidental old 6h build will fire. Record exact commit SHA and GitHub quality run.
- **FIRST real hosted diagnostic:** dispatch ONE `preflight_only=true` workflow for its exact current main SHA, with `run_native_build=true` but all three native/package jobs forced skipped; confirm hosted preflight PASS, generated ZIP source patch and capacity measurements PASS, and actual skip via job table. If FAIL, STOP with exact error and return to independent audit, no more attempts.
- If the diagnostic PASSES and the conda native lock still matches, **resume original owner's still-pending actual native work** by dispatching ONE corrected `preflight_only=false` *cold* workflow for exact implementation SHA. This is the audited remediation of a setup-only failure, not a blind repeat of any OCCT/pywrap build: old run produced no native artifacts. Stage A OCCT SDK with durable artifact; stage B official 315-module generated source native compile (NO PYWRAP), stage C packaging/clearance/installer. Treat every stage as hard STOP on failure. Do not start a second cold run, auto-retry failure, or increase workers/timeout to hide a blocker.
- If cold pipeline reaches real installer and all gates PASS, run at most ONE separate genuine cache-HIT proof. If still blocked at any phase, publish actual job URLs/artifacts/checkpoint hashes and stop; do not fabricate distribution evidence.
- **Do not start PL-0351, M17, or PL-0368**, do not sign/public release, do not change source license obligations, do not include opaque wheel native binaries in produced runtime. Do not modify root TASKS.md or independent ChatGPT audits.
- Full original owner approval and preflight audit references apply. The point of this R01 is to fix 3 bootstrap strings, verify native conda Python remains exactly 3.12.15, and complete the same blocked PL-0350 route without further arbitrary V-number churn.

## Handoff

Publish log:
`coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CODEX_LOG.md`
Report:
`coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_REPORT.md`
Update existing PL-0350 hosted master handoff log **only as builder-owned log evidence** if necessary; never modify auditor tracker/criteria. Record GitHub URLs for PRE-FLIGHT ONLY and COLD and optional WARM, job logs, result, exact source/build/asset hashes and artifacts (or absence), Python 3.12.10 bootstrap vs 3.12.15 conda assertions, capacity/free disk, all test pass/fail and Git parity.

If preflight fails: `BATCH_STOPPED_AT_PL-0350 / PRE_FLIGHT_<reason>`. If cold fails: `BATCH_STOPPED_AT_PL-0350 / <STAGE>_<reason>`. If all source/provenance/installer and cold+HIT gates PASS: `READY_FOR_INDEPENDENT_PL0350_AUDIT`. Never claim completed installer unless the file genuinely exists with SHA and actual GitHub Actions artifact.
