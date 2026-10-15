# PL-0353 | ChatGPT Independent Audit Criteria V02 — Private CI, No Proprietary Sample Dependencies

Owner's actual repository is **PRIVATE**, not public, but user/product/supplier/POVU scan data must not be packaged into CI, and no public release or Kenya factory rollout is authorized. V02 supersedes old public-repository assumption of PL0353 V01. Execution authority: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_CODEX_PROMPT_V02.md

**AUDIT PASS gates:**
1. Independently enumerate default hosted Quality/test workflow(s), hosted packaging/smoke, file inputs, fixture trees, generated outputs and upload paths. Demonstrate no runtime dependence on owner-specific `C:\Users`, personal/OneDrive/AppData/private scan roots or external private datasets.
2. Default CI can execute from clean Windows checkout with small tracked public/synthetic data or deterministic generated fixtures only; actual hosted runner execution SUCCESS with new pass/skip counts after work, not recycled PL0350 runs. No use of an owner-worktree/source tree as implicit dependency.
3. Tests depending on authentic private scans are explicitly opt-in and absent from default CI, with truthful skip/gate. No fabricated geometric accuracy, M17 golden benchmark or reconstruction performance PASS.
4. Fail-closed, testable guard inspects actual reachable committed/staged/packaging/artifact upload boundaries; catches known prohibited private-scan/supplier-image data paths, large unknown raw scans and escaping symlinks without blocking needed approved tiny synthetic PNG/STL/STEP/DXF fixtures or required notice/source texts. Negative canaries synthetic, not real owner files.
5. No prohibited private bytes or sensitive absolute owner paths in Git logs or artifacts. Private repository is not a substitute for safe data stewardship.
6. Existing `PL0352` private retained Installer checkpoint ID `11959245441` and `PL0351` portable installer smoke are preserved; no native OCCT/OCP/Installer compilation, binary alteration, new signing/public release, duplicate huge archive or shared-cache changes.
7. Workflow safety: manual native build remains manual-only, verified job trigger graph, least-privilege actions SHA pinning and no implicit 6-hour rerun. Quality host can run independently.
8. Local relevant focused pytest, Ruff/format/mypy and YAML parse valid. Full hosted Quality only once if needed, and measured real test totals. Old 2158 count is historical.
9. Codex does not touch root TASKS.md, owner Desktop, OwnerDev, installer/SDK/OCP checkpoint, M17 or PL0354+ scope; separate implementation commits and V02 log-only published with run links to private main, ends READY_FOR_INDEPENDENT_AUDIT.
10. Product remains proprietary internal Kenya factory planned use; `legal_review_required=true`, `public_release_authorized=false`. Passing data hygiene does not grant release, legal opinion, or factory authorization.

**PARTIAL/BLOCKED:** no real hosted clean Quality verification, ambiguous private scan dependency, guard bypass or missing local evidence. **FAIL:** asserts PASS using owner-only scans, leaks private material, re-runs native compiler, modifies unrelated projects or changes user binaries, or fabricates coverage.
