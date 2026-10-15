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
