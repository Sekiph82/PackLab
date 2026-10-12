# PL-0350 — ChatGPT Independent Audit of R01 Bootstrap / Hosted Cold Stop

Date: 2026-10-12
Verdict: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Handoff: **BATCH_STOPPED_AT_PL-0350 / OCCT_SOURCE_FETCH_FAILED_TO_IMPORT_TOOLS**
PL-0350: **NOT COMPLETE**. No source-built OCCT SDK, OCP native extension, Studio installer, clearance, or warm cache-HIT result.

## First-hand evidence examined

- R01 implementation: https://github.com/Sekiph82/PackLab/commit/fe87cd03ba5455eda6bf6d2851335e6eae93d47b
- R01 evidence publication: https://github.com/Sekiph82/PackLab/commit/ca828a1e4a2b724fc41bca412fe6babf3a766048
- R01 log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CODEX_LOG.md
- R01 blocker report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_REPORT.md
- Master handoff: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Diagnostic-only Actions run: https://github.com/Sekiph82/PackLab/actions/runs/38257424866
- Cold Actions run: https://github.com/Sekiph82/PackLab/actions/runs/38257727675
- Native OCCT job: https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114840209934
- Quality Actions: https://github.com/Sekiph82/PackLab/actions/runs/38256982630
- Exact current workflow: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml
- Importing source script: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/fetch_verify_windows_native_sources.py
- Native source-lock validator: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/validate_windows_native_source_lock.py

Independently fetched and inspected live R01 reports, revision diffs, actual GitHub Actions job table and **actual failed OCCT job logs**, related Python tool scripts, and workflow code. Actions artifact listings for both R01 diagnostic and failed cold run contain **zero** items. Current `main` was `ca828a1e...` when review started. The builder's reported Git working tree state on the user Windows computer was not independently executed by this audit.

## Findings

**F01 — R01 bootstrap repair and guarded preflight: PASS.**

- 3.12.10 Windows-hosted `actions/setup-python` succeeded in actual diagnostic and cold jobs, without mutating the frozen native 3.12.15 conda lock.
- Diagnostic-only job `114839019830` passed; jobs OCCT/OCP/Studio all `skipped`.
- Cold capacity-preflight `114840035571` passed; code/runner reports show the official generated-source 319→315 No-VTK patch checks passing. Actual numeric capacity values are in the remote job step summary, not independently extracted from logs; do not invent storage figures.
- Cold OCCT job `114840209934` created the exact conda-forge native Python 3.12.15 and libpython packages and passed the explicit native version identity assertion; SDK cache miss was verified.
- GitHub Quality `114837468064` at exact R01 implementation SHA passed. Builder's focused CI workflow test 4 PASS and static checks passed; no full-suite rerun this time is accurately disclosed.

**F02 — hard blocker is Python CLI import mode, NOT source archive corruption.**

The actual OCCT job tried:
`uv run --locked python tools/packaging/fetch_verify_windows_native_sources.py --download-dir ... --evidence ...`

The script's line 12 imports:
`from tools.packaging.validate_windows_native_source_lock import load_source_lock`

Direct file-path Python invocation uses the script directory for `sys.path[0]`, and the standalone workflow step **does not** set `PYTHONPATH` to the repository root. Actual runner exception:
`ModuleNotFoundError: No module named 'tools'`.

PowerShell's next message, `A locked corresponding-source archive failed verification`, is only a generic wrapper. **The script never downloaded/verified an archive; source hashes never failed.** GitHub's OCCT cache was a MISS (recorded key `Windows-x64-occt-sdk-v2-2be7a8bdc7e5cf5fbe52770b19c7d6324a057900f7c64f1e5cd84ca7a53666e4`), and no SDK was sealed.

**F03 — systemic reoccurrence risk: many more direct-script calls.**

The same workflow contains at least 17 `uv run --locked python tools/packaging/...` and 3 `micromamba run -n packlab-ocp-bindings python tools/packaging/...` invocation sites; several corresponding scripts use absolute `tools.packaging.*` imports. Only some steps set `PYTHONPATH`. Fixing just the failing source-fetch step would very likely produce the same class of error at later SDK validation, OCCT build, OCP builder, packaging or runtime checks.

**F04 — heavy stages not reached and no second attempt.**

No OCCT native compilation, durable SDK checkpoint, OCP C++ extension, sealed runtime, production packaged smoke, redistribution inventory or installer. OCP and packaging were skipped and warm run never started. Native build remained manual-only with exact SHA, no accidental automatic heavy producer. Desktop/OwnerDev preserved per builder report. No reason to rerun five-hour pywrap or downgrade source locks.

## Required focused remediation, SAME PL-0350

**Correct all workflow invocations that depend on repository-local package imports, not only the first exception.**

Preferred: invoke root-locatable repository modules using `python -m tools.packaging.<module>` (with `uv run --locked` or `micromamba run -n packlab-ocp-bindings` as appropriate), from the repository root; make required repo root `PYTHONPATH` explicit where subprocesses/import context need it. Validate package entrypoints and side effects. Keep importer/validator source lock, pinned native Python 3.12.15, exact 315 No-VTK source contract, four-worker limits, hash manifests and manual-only native trigger unchanged.

Before another cold run, implement **fast hosted import-only smoke** (fresh Windows-2022 runner + locked uv/native Python) over *all* workflow-invoked `tools.packaging` scripts, including Python module resolution and argument parser `--help` where safe. This smoke must NOT download large source archives or run native compilation. Add real subprocess tests from repository root and a deliberately isolated script-path invocation to prove the regression and the correction; assertions must reject remaining vulnerable direct-script invocations. Preserve a preflight-only mode that skips all OCCT/OCP/Studio jobs.

Run one controlled **diagnostic-only import/provenance validation** first, and only if green one corrected hosted cold attempt under the existing owner's PL-0350 source-built authorization. If it later fails, **stop** with the exact first new blocker and preserve prior completed artifact checkpoints; no automatic retry/rebuild loop.

Focused remediation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_CODEX_PROMPT.md

Matching audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_CHATGPT_AUDIT_CRITERIA.md

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`. R01's bootstrap repair is accepted as effective, and the cold run failed on an **early configuration/import error**, not on a CAD compiler or native binary defect. Do not mark PL-0350 PASS, do not touch root `TASKS.md` from Codex, do not start PL-0351/M17/PL-0368, and do not claim Installer availability. Production completion still requires actual hosted native binary and distribution/installer evidence.
