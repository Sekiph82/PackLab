# PL-0350 R02: Python module import repair

Authority: existing owner-approved 315-module No-VTK GitHub-hosted native build. Task stays PL-0350.

Independent audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SETUP_PYTHON_R01_CHATGPT_AUDIT_V01.md

## R02 instructions for Codex

1. Fetch and review current origin/main TASKS.md, preserve the user's dirty Desktop checkout and known-good PackLab.exe. Do not edit root TASKS.md or ChatGPT audit documents.
2. Fix verified hosted error in run 38257727675. Source fetch failed at line 12 because direct execution of `tools/packaging/fetch_verify_windows_native_sources.py` did not resolve the `tools` repository package. Source downloads did not start and OCCT/OCP compilers did not run.
3. Audit EVERY Python script invocation throughout `.github/workflows/windows-studio-build.yml`, including OCCT, OCP and Studio packaging. Convert repository-local script entrypoints to `python -m tools.packaging.<module>` from checkout root, preserving uv or micromamba environment as appropriate. Where needed, set PYTHONPATH to the validated checkout root. Ensure actual module CLI functionality is unchanged. Do not fix just the first failure.
4. Add executable lightweight regression tests that run the real entrypoints using `-m`, verify all workflow calls, and reject unguarded direct file-path invocations. Test on a fresh temporary Python process, including a script-path reproducer of the old failure and a module-invocation success. Cover all repository-importing scripts without fetching native source or compiling.
5. Keep workflow manual dispatch only and existing `preflight_only` heavy-job skip. Extend preflight with a quick hosted module-import smoke that runs with zero native compilation or large download. Prove the smoke and all native-job skip rules with tests before any cold run.
6. Preserve locked bootstrap Python 3.12.10, native conda Python 3.12.15, exact source hashes, 315 No-VTK module patch, source provenance, four-worker cap, stage manifests, compliance gates and unsigned installer contract. No five-hour pywrap regeneration or prebuilt OCP-wheel substitution.
7. Test with bounded local unit/quality checks, without large local native builds. Publish implementation to GitHub main only after verifying the heavy workflow remains manual-only and quality CI stays enabled.
8. Run one quick manual preflight-only hosted diagnostic for the exact new SHA. If it fails, STOP. If it passes, continue the owner-approved source-locked hosted pipeline with ONE cold run: source fetch and sealed OCCT SDK, then 315 OCP compilation, then actual CAD/PDF/Open3D packaging and unsigned Installer. Stop at the first real failure and retain completed checkpoints. Only run one warm-cache proof after full cold success. No blind retry.
9. Protect owner checkout and runtime, and do not advance PL-0351 or M17. Record exact run URLs, job results, tests, artifacts, hashes and any blocker.

Logs to publish: `coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_CODEX_LOG.md` and `PL-0350_REPO_IMPORT_PATH_R02_REPORT.md`. Update the builder-owned master log if needed. Finish AWAITING_INDEPENDENT_AUDIT, or READY_FOR_INDEPENDENT_PL0350_AUDIT only if an actual cleared installer and cold/warm proof exist.
