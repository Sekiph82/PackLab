# PL-0350 — 315-Module No-VTK Prebuild ChatGPT Audit Criteria

Owner decision: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_DECISION_NOVTK_315_MODULES.md
Codex prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CODEX_PROMPT.md
Scope: *static/preflight only*. PL-0350 remains unchecked; no native-build authorization.

1. Fetch/sync origin/main non-destructively, preserve dirty Desktop and previous-good OwnerDev, active processes, protected cache. Codex never edits root TASKS.md, owner decision, or ChatGPT audits.
2. Verify ALL GitHub workflow push triggers BEFORE modifying any path. No product/native packaging workflow triggered by this docs-only publication; no changes to tools/packaging/**, tests/ci/**, workflow YAML, app/core/source locks or any other path that triggers costly Windows production. Do not rely on skip-ci or timeout to interrupt it.
3. Exact official ZIP SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b` / source tag `d69b064...` / 6,481,047 bytes pinned; no alternative artifact accepted silently.
4. Input inventory 319 module triplets with matching registration consistency, output static patch plan yields 315 and **only** excludes `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK`. No VTK CMake references or missing/truncated non-VTK generated inputs. Identical source hashed before/after or patch digest recorded. Runtime `__version__` vs package version mismatch explicitly handled.
5. PackLab CAD, STEP, DXF, geometry and dynamic-import scans confirm all required used import modules present within 315; any unresolved dynamic usage reported, not declared PASS by inference alone. Tiny tests for no-VTK patch and consistency, not costly builds.
6. Stage design accounts for <=6-hour GitHub-hosted cap per job, known ~43-minute OCCT stage, unknown OCP native compile, preverified release ZIP, file-by-file sealed output hashes, exact caching, artifact transfers and preservation of complete 315 CAD functionality.
7. All existing copyright/third-party-source mapping and 79 OCP opaque wheel rows remain OPEN until genuine audited evidence; no PyPI-wheel substitution, no fake license closure. QtPdf/Open3D packaged smoke and installer clearance still future separate gates.
8. No native build, pywrap generation, Actions dispatch, packaged EXE/installer, OwnerDev refresh or multi-gig test performed or claimed. <=200MiB scratch for short validation and truthful disk/free-space evidence, no fresh giant local checkout.
9. Report/log published with scoped PASS/FAIL source and exact GitHub links; origin/main parity, root TASKS and owners work preserved.
10. Close **only** prebuild static inspection, if green; owner explicitly approves any future native hosted build in a separate decision. Any hidden native build means audit FAIL. PL-0351 blocked, no M17, PL-0368 deferred.
