# PL-0350 — ChatGPT Independent Audit V07

Date: 2026-10-10
Decision: **AUDITED_CHANGES_REQUIRED / HOSTED_JOB_LIMIT**
Implementer handoff: `BATCH_STOPPED_AT_PL-0350_V07`
Child: `READY_FOR_INDEPENDENT_AUDIT`

## Independent evidence inspected

- V07 implementation: https://github.com/Sekiph82/PackLab/commit/1f45e61f3743879301528157f047b6415cbac9bf
- V16 R08 preceding behavior gates: https://github.com/Sekiph82/PackLab/commit/408dae870859268876693c182054bb48c3a24517
- Child log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V07.md
- V16 master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_R08_DISK_REMEDIATION_PL0350_V07_CONTINUATION_CODEX_LOG_V16.md
- Exact production run: https://github.com/Sekiph82/PackLab/actions/runs/37967978530
- Quality: https://github.com/Sekiph82/PackLab/actions/runs/37967978536
- Source/build scripts: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml and https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_runtime.py
- Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V07.md

Direct GitHub Actions API inspection confirms producer job `113947049711` is `cancelled`; the build step was cancelled, all bundle validation/cache-upload steps were skipped, and package job `114118446494` was skipped. GitHub API artifact listing for the exact production run returns **zero artifacts**. Quality job `113947049677` succeeded. Downloaded and examined actual hosted producer job log, not only Codex's summary; cancellation and OCCT/pywrap timings match the log.

## Confirmed findings

**C01 — verified runtime build design now compiles generated project, but cold build exceeds hosting budget.**

The separate generated OCP CMake project compilation fix exists in commit 1f45e61. Source-lock and bound four-worker settings are present, and actual hosted producer reaches the real generated source compilation stage. Actual host timing:

- OCCT native build: **2,560.860 s** (~42m 41s).
- pywrap generation: **18,220.375 s** (~5h 03m 40s).
- generated native C++ binding compile: started ~03:06:53Z; at 03:15:23Z was still compiling `BRepAlgo_pre.cpp`.
- producer job cancelled at six-hour GitHub-hosted job ceiling with no fatal compiler diagnostic earlier.

Thus the *job architecture*, not a proven CAD code defect, is blocking. The workflow states `timeout-minutes: 480`, but this does not supersede the platform's **six-hour hosted job limit**. Raising it further is not a solution.

**C02 — no product artifact or distribution proof.**

No sealed OCP bundle, verified cross-run cache save/hit, same-run artifact, packaged QtPdf/OCP/Open3D smoke, distribution clearance, or unsigned installer resulted from the exact run. PL-0350 must remain unchecked. PL-0351 cannot begin.

**C03 — local Windows quality and working owner EXE accepted as *builder-observed* evidence.**

Full suite 2,055 passed / 11 skipped / 1 deselected under monitored wrapper; focused 25 passed, mypy 232 files, compileall, changed-code Ruff and quality Actions passed per logs. OwnerDev launcher reopened with reported SHA and responsive window. No clean-install portability was claimed. Two repo-wide Ruff findings in untouched preview code remain separately noted, not concealed. This audit did not independently execute the owner's Windows runtime.

**C04 — R08 core disk safety remediation substantially resolved.**

Reviewed newly added true tiny-quota Windows behavioral tests, fixed live disposable-path scanning, and null-safe stream EOF. The prior 65-GB-class test amplification is not repeated in this run; builder reports ~55.25 MB peak. Shared uv-cache consumers and legacy AppData were preserved. Legacy AppData per-directory read-only measurement/owner attribution remains maintenance-deferred, not silently considered zero bytes; do not block hosted CI exclusively on protected/shared-cache state.

## Required architecture correction within SAME PL-0350 task

Do **not** retry the same monolithic six-hour cold job. Do not increase N_PROC above the source-locked 4, delete unrelated caches, or move a large build onto the owner's C: drive.

Keep source-built OCP/OCCT provenance and split into **durable, hash-verified per-phase GitHub-hosted jobs/checkpoints**:

1. OCCT source build/install, seal exact verified SDK/runtime artifact and cache it.
2. pywrap generation from exact OCP/pywrap source lock + restored verified OCCT SDK. Seal exact generated C++/CMake project and minimal required build inputs; job must not repeat OCCT build.
3. configure/compile generated extension from validated intermediate artifact; seal complete runtime OCP/OCCT package + metadata; job must not repeat pywrap or OCCT.
4. final source/notice/compliance inventory, packaged full-capability smoke and unsigned installer via separate packaging job.

Each job has its own <=6-hour effective GitHub-hosted window, exact sha256 manifests, exact-input cache keys, no unsafe fallback restore, same-run validated artifact handoffs, explicit provenance verification. The pywrap stage takes about 5h04m based on live evidence, so budget preflight MUST confirm enough headroom for setup+upload; otherwise first optimize or split its work again safely without weakening the 319-module contract. Verify generated artifacts are portable to fresh runner paths; never trust CMake stale absolute cache paths. Check actual artifact size/limits/storage before multi-hour run. Stage checkpoints survive a downstream cancellation and are reusable without repeating expensive preceding stages.

Only after the new architecture passes static/small-fixture provenance/transfer tests may **one** cold hosted phase-split build be launched. Subsequent exact-input cache HIT proof must also be real; if blocked, stop at exact phase with measured logs and do not fabricate an installer.

The next remediation is **PL-0350 V07-R01 phase-split**, not a new unrelated milestone or an endlessly raised timeout.

## Verdict

`AUDITED_CHANGES_REQUIRED` for PL-0350 V07. Accepted frontier remains PL-0347 V02 through PL-0349 V03. PL-0351 onward unstarted; PL-0368 DEFERRED_POST_M17. Preserve working owner Desktop EXE.
