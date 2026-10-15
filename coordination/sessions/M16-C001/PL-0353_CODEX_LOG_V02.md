# PL-0353 Codex Log V02 — Safe CI Without Proprietary Sample Data

**Result: READY_FOR_INDEPENDENT_AUDIT**

## Scope and authority

Executed PL-0353 only, under the V02 master prompt and its matching audit criteria. Read the live `TASKS.md` status, V01 prompt and criteria, V02 criteria, governance documents, and predecessor audit evidence. The managed checkout began synchronized to private `origin/main` at `7fcd4170647d021ea94120b5f39b897728ac93db`; no unexpected divergence was present. All implementation and verification were performed in the task worktree. The owner Desktop checkout and files were not edited.

`TASKS.md`, ChatGPT audit files, PL-0354+, M17, and PL-0368 were not modified. No production Installer, OCCT, OCP, SDK, or PL-0351/PL-0352 acceptance build was rerun. The Studio Build workflow remains manual-only and was not dispatched.

## Files changed

- Workflows: `.github/workflows/windows-python-quality.yml`, `.github/workflows/packlab-preview-windows.yml`, `.github/workflows/windows-studio-build.yml`, `.github/workflows/pl0350-fmt-dependency-probe.yml`, `.github/workflows/pl0350-sdk-checkpoint-recovery.yml`.
- Guard and policy: `tools/ci/ci_data_safety.py`, `tools/ci/ci_safe_data_policy.json`, `tools/ci/scan_artifact_inputs.ps1`, `tools/ci/__init__.py`.
- Fixtures/tests: `tests/fixtures/ci-safe-synthetic/` (README and six small deterministic PNG, JPG, STL, PLY, STEP, and DXF fixtures); `tests/ci/test_ci_data_safety.py`, `tests/ci/test_windows_python_quality_workflow.py`, and `tests/ci/test_windows_studio_build_workflow.py`.
- One narrow cross-task CI repair: `tools/packaging/pl0352_artifact_retention.py` now rejects a missing/non-string expiry before parsing. This preserves the existing `invalid_expiry` fail-closed behavior and fixes the existing hosted Mypy error; it changes neither the retention workflow nor any artifact.

## Data-flow and guard result

- Windows Quality starts with a clean Windows-hosted checkout, blanks ambient Python/Qt/Conda and PackLab data-root variables, and runs the data guard before installing the locked environment. Its default test inputs are committed small synthetic fixtures or deterministic test-temporary files. The default suite does not acquire owner, supplier, POVU, Kenya customer, Desktop, mounted-drive, or sample-scan data.
- The Studio Preview workflow has push-path and manual triggers. Its clean hosted job runs the tracked-source/environment guard before its standalone preview build and checks the resulting EXE and separate preview setup executable before upload. Its uploaded preview artifact is configured for one-day retention.
- The Windows Studio native build is `workflow_dispatch` only. Added guards cover the actual stage directories and artifact upload inputs. The PL-0350 dependency-probe and SDK-recovery upload boundaries are also guarded without adding triggers. PL-0351 smoke and PL-0352 retention workflows remain manual; no retention upload or Installer readback workflow was dispatched.
- The fail-closed scanner rejects private-data path families, raw scan formats, unapproved sensitive media/CAD/document payloads, oversized unknown raw and structured files, unsafe archive members, escaping symlinks/junctions, owner-specific workflow roots, tainted developer-runtime environment variables, and owner roots in uploaded text diagnostics. Its failure output contains codes and a safe extension category only, never paths or content. Exact SHA-256/size policy entries permit the six synthetic fixtures and existing calibration/branding assets. Text CAD/mesh/SVG hashes use LF canonicalization to remain exact across Windows and Linux checkout line endings; binary images and the icon remain byte-pinned.
- Negative canaries cover supplier/customer/POVU/OneDrive/Dropbox/private paths, raw scans, unexpected images/documents, oversized data, unsafe ZIP contents, environment injection, owner paths in workflow/diagnostic text, changed allowlisted bytes, and symlink/junction escapes. Positive checks cover the approved synthetic media, text fixtures, and matching-source notices.
- Static source review found a local-only `tools/sync_from_github.ps1` default path; it is not referenced by CI workflows or test/build commands. Other owner-like path strings found under tests are synthetic canaries. No CI input edge uses that local helper.

## Verification

### Local

- Focused tests: `uv run pytest tests/ci/test_pl0352_artifact_retention.py tests/ci/test_ci_data_safety.py tests/ci/test_windows_python_quality_workflow.py tests/ci/test_windows_studio_build_workflow.py -q` — **68 passed**.
- Targeted Mypy: `uv run mypy tools/ci/ci_data_safety.py tools/packaging/pl0352_artifact_retention.py` — pass.
- Ruff lint and changed-Python formatting (using the workflow's `format.line-ending = 'auto'` setting) — pass.
- YAML parse: all eight `.github/workflows/*.yml` files parsed successfully with PyYAML 6.0.3.
- `compileall` on the changed Python files — pass.
- `python -m tools.ci.ci_data_safety --repository . --tracked --check-workflows --check-environment` — `PACKLAB_CI_DATA_GUARD=PASS`.
- `git diff --check` — pass; working tree clean before this log-only change.

### Hosted

- Windows Quality run [38713322342](https://github.com/Sekiph82/PackLab/actions/runs/38713322342) on final implementation SHA `68a560e446070b938c31eb2595056448123d612f` — **SUCCESS**. Guard passed; Ruff passed; Mypy reported no issues in 254 source files; default suite: **2,218 passed, 10 skipped, 1 deselected, 2 warnings** in 201.96 seconds.
- Studio Preview Windows run [38712670742](https://github.com/Sekiph82/PackLab/actions/runs/38712670742) on guard-complete SHA `899fad9fad26e84968f8b0fd1e89967296e8beda` — **SUCCESS**, including clean-runner guard, standalone preview EXE/setup build, and artifact-input guard. The later change to the unrelated retention-expiry type guard did not alter preview workflow inputs or implementation.
- Initial hosted attempts failed closed before dependencies or package upload: runs `38711663045`, `38712253714`, and `38712484163` identified Windows checkout line-ending differences in approved SVG and synthetic STEP/PLY/STL files. The allowlist hashes and regression tests were corrected with newline-canonical hashing. Run `38712666169` completed the suite (same 2,218/10/1 result) but Mypy found the pre-existing optional `expires_at` typing issue in the retention validator; the narrow string guard above fixed it. No failed run uploaded a product or proprietary sample artifact. Final hosted run and preview build succeeded.

### Retained artifact and repository state

- Repository visibility verified `private=true`; default branch is `main`.
- Private retained Installer artifact **11959245441** was rechecked: `expired=false`, 877,601,969 bytes, SHA-256 `b976c7d4e48985329c8f51a68b250ff6e565930ed993b0409b9c5d561c3da4ac`, expiry `2026-12-14T08:38:33Z`, original run `38707054365`. It was neither downloaded, reuploaded, nor modified.
- Legal boundary remains unchanged: `legal_review_required=true`; `public_release_authorized=false`. This CI result grants no release or factory-deployment authorization.

## Commits and publication

Implementation commits pushed fast-forward to private `main`:

- `1fa2ae1a49cb031ef462d82e07d2a09ef3a5cd8a` — initial CI data-safety scanner, workflows, tests, fixtures.
- `d906ff5c3b5769b7c7937a2db6f18184e2e6ea78` — canonical SVG hashes.
- `5445c608ed50569fd396122d827d9dd3644fe3e8` — path-free payload-category diagnostics.
- `899fad9fad26e84968f8b0fd1e89967296e8beda` — canonical synthetic CAD/mesh hashes.
- `68a560e446070b938c31eb2595056448123d612f` — fail-closed expiry type guard for hosted Mypy.

The V02 Codex log is published as a separate log-only commit. `origin/main` is the publication ref. No secrets, private scans, customer data, supplier documents, private path values, or owner binaries were added.

## Handoff

`READY_FOR_INDEPENDENT_AUDIT`

## PL-0353-R01 remediation addendum — fail-closed upload gates

**R01 result: READY_FOR_INDEPENDENT_AUDIT**

### Scope, synchronization, and preservation

Executed the R01 remediation prompt at `coordination/sessions/M16-C001/PL-0353_R01_FAIL_CLOSED_UPLOAD_GATE_CODEX_PROMPT.md` and checked the matching PL-0353 audit context. At remediation start, the worktree was synchronized after a safe fast-forward from `6b7f32d` through `a3ec18e3` to current private `origin/main`; no local changes were reset or discarded. The existing V02 log content above is retained verbatim. The R01 implementation is commit `ba6b4b0647ee69d8ef1320717ea257ce468eac45`.

`TASKS.md`, audit verdicts, Desktop files, and the retained Installer were not modified. No OCCT/OCP/native compilation, Installer rebuild, full-suite rerun, cleanup, or hosted build workflow was performed. The repository remains private.

### Guard remediations and workflow audit

The four confirmed unsafe pairs now bind every corresponding uploader to the exact preceding guard step's successful outcome:

- Studio precompile diagnostics: `guard_precompile_diagnostics` → `upload-precompile-diagnostics`.
- OCP quarantine diagnostics: `guard_ocp_quarantine` → `upload-ocp-quarantine-diagnostics`.
- Studio smoke diagnostics: `guard_studio_smoke_diagnostics` → `upload-studio-smoke-diagnostics`.
- FMT dependency probe report: `guard_fmt_probe_artifact` → `upload-fmt-dependency-probe`.

A workflow-wide audit found one additional analogous `always()` bypass in pre-clearance evidence upload; it is also fixed with `guard_preclearance_evidence` → `upload-preclearance-evidence`. Each upload condition explicitly uses `always() && steps.<guard-id>.outcome == 'success'`. Existing diagnostic inventory/size predicates and upload action pins, artifact names, retention periods, and payload inputs were preserved.

Parsed and reviewed all eight GitHub Actions workflow YAML files and all artifact-upload/status-override combinations. Exactly these five uploads use status-function overrides; each now requires its own identified guard to succeed. The other artifact uploads retain default success gating or depend on ordinary outputs, so prior failures suppress upload. Uploads configured with missing-file warning/ignore behavior were checked for an independent guard-success condition. Other always-run steps were inspected: they are fail-closed summaries/validators or diagnostic collection and do not create an upload bypass.

### Focused regression and static checks

- `uv lock --check` — pass.
- `uv run --locked --group workflow-tests pytest tests/ci/test_artifact_upload_guard_conditions.py tests/ci/test_windows_studio_build_workflow.py -q` — **22 passed**. Regression coverage evaluates guard failure, skipped/absent outcomes, safe diagnostics after unrelated earlier failures, the five exact upload/guard pairs, and discovery of status-overridden uploads across all workflows.
- Ruff lint for the new tests and workflow contract test — pass.
- Ruff formatting check using workflow line-ending configuration — pass.
- `uv run mypy tools/ci/ci_data_safety.py tools/packaging/pl0352_artifact_retention.py` — pass.
- `compileall` on the new regression test and scanner — pass.
- PyYAML structured parse of all eight workflow YAML files, including preservation of the `on` key — pass.
- `python -m tools.ci.ci_data_safety --repository . --tracked --check-workflows --check-environment` — `PACKLAB_CI_DATA_GUARD=PASS`.
- `git diff --check` — pass.

No full default suite or hosted CI was repeated: the narrow R01 conditions were exercised by focused regression tests, and the prior V02 hosted Windows Quality/Preview evidence remains as recorded above. No Installer/OCCT/OCP workflow was dispatched.

### Retained artifact, privacy, and boundaries

The retained Installer remains artifact `11959245441`; prior metadata in the V02 verification records it as unexpired with SHA-256 `b976c7d4e48985329c8f51a68b250ff6e565930ed993b0409b9c5d561c3da4ac`. It was not downloaded or changed during R01. The data-safety guard passed on the tracked checkout. No secrets, proprietary sample scans, owner path values, or private files were included in commits. This workflow-gating remediation is not a legal redistribution clearance, product release authorization, or factory deployment approval.

### Publication and handoff

The R01 implementation was pushed to private `main` as `ba6b4b0647ee69d8ef1320717ea257ce468eac45`. This addendum is to be published in the separate log-only commit. No `TASKS.md` change is part of this work.

`READY_FOR_INDEPENDENT_AUDIT`
