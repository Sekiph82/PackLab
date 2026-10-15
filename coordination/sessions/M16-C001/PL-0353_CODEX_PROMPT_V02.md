# PL-0353 | ONE-SHOT CODEX MASTER V02 | Safe, Self-Contained CI Without Proprietary Samples

Task: **PL-0353** only. Project: PRIVATE proprietary `Sekiph82/PackLab` repo; Kenya factory internal commercial use is the intended scope. No public release, no new user-owned dataset uploads, no factory deployment, no release permission.

## Authority

Read live root `TASKS.md` (ChatGPT-only lifecycle), historical `PL-0353_CODEX_PROMPT_V01.md` and `PL-0353_CHATGPT_AUDIT_CRITERIA_V01.md`, and current ChatGPT V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0353_CHATGPT_AUDIT_CRITERIA_V02.md

Predecessor independently verified:
- PL0350 Installer technical PASS: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_V02.md
- PL0351 portable installed smoke PASS: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CHATGPT_AUDIT_V01.md
- PL0352 private retained Installer readback PASS: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0352_CHATGPT_AUDIT_V01.md

## Objective

**Prove that current supported Windows CI/test/packaging/smoke operates using committed safe synthetic/public fixtures and generated small deterministic test data, never secretly relying on owner Desktop, private sample scans, Kenya customer/POVU datasets, supplier documents, proprietary images, personal location/user file paths, or mounted external drives.** Make build and test failure truthful: missing proprietary data must not produce false green acceptance. This is a CI-safety/portability scope ONLY, not accuracy benchmarking (M17).

### Stage 1: Read-only dependency/data-flow audit FIRST

1. Inspect existing workflows (Windows Quality, Windows Studio packaging/preflight, PL0351 fresh installer smoke, PL0352 preservation, and actual existing preview workflows) and current `tests/**`, `tools/**`, packaging commands, build-smoke fixtures, CI artifact upload paths.
2. Map every actual filesystem input (fixtures, scans/images, generated outputs, data download, cache, environment, secrets) into (a) source-tracked/reviewed synthetic/public small fixture, (b) deterministic transient generated minimal sample, (c) separately authorized third-party upstream source/dependency fetched by exact lock, (d) forbidden owner/private/supplier/proprietary data, (e) unknown/ambiguous BLOCKED.
3. Respect owner prior private project policy and restrictions: a **PRIVATE** repo does not make personal/customer/supplier assets automatically CI-safe. Existing PackLab source and bundled legal-source evidence stay under their own verified provenance, but no product test scan is silently imported.
4. Look for hardcoded `C:\Users\...`, OneDrive, Dropbox, network shares, /mnt, AppData, previous owner's worktrees, arbitrary user profile, external scan roots, wildcards that accidentally package scanned media, installer test data and background network downloads.
5. Prioritize actual reachable build/test code, then lightweight static scanning of tracked/project-scoped files; do NOT walk entire owner C: or materialize any private scan. Do not use large scans or data as surrogate fixtures.

### Stage 2: Minimal implementation + fail-closed protection

1. Add/reuse a bounded CI-safe scanner and provenance policy as needed: detect forbidden private data *families and dangerous packaged payloads* using actual extension/folder/scope/size rules with documented exemptions. Distinguish safe user-created synthetic tiny `.png/.jpg/.stl/.ply/.step` fixtures from real media/scan sets. Avoid blanket blocking normal legitimate source code or tiny fixtures.
2. Ensure **default tests pass on a fresh isolated Windows CI checkout** with no mounted user data, no repo-local proprietary scans, no ambient hidden artifacts, and no developer `PYTHONPATH`/Qt/Conda helper injection. No silent skip on missing private data: tests requiring data use deterministic synthetic fixtures, else explicitly opt-in outside default CI and display transparent SKIP/BLOCKED reason.
3. No test should connect to user directories, acquire sample files or download runtime data. External source dependencies in build jobs remain only existing locked/pinned reviewable sources, not hidden runtime fetch in packaged application.
4. Scan all **actual uploaded binary/diagnostic artifact inputs**, tracked file additions, and CI build staging for accidental private scan contents and forbidden filenames/path patterns. Fail closed with redacted concise diagnostic; avoid logging sensitive absolute paths, hashes tied to owner's data, image contents or file bytes. Quarantine/drop only generated CI outputs when confidently in scope, never delete owner Desktop files.
5. Tests for negative cases: injected obvious private-data canary (fake synthetic data only), owner-path-dependent test, unexpected huge scan, private supplier/POVU art, hidden location root, unsafe upload path, symlink/junction escape where relevant; positives for needed small synthetic images/meshes/STEP/DXF and matching-source notices. Never print or upload actual private data.
6. Preserve source-locked OCCT/OCP/Installer artifact and private-retention lineage. **Do NOT rebuild them**, re-run the already accepted PL0350/PL0351 builds, or delete/invalidate private retained artifact ID `11959245441` expiring 2026-12-14 08:38:33 UTC.
7. One bug pre-noted for later maintenance: PL0352 audit states original retention-source artifact expires earlier, hence 60-day retained archive is not permanent and the old bridge cannot necessarily renew it. Do NOT create a new retention bridge, extra 0.88GB Installer copy or billing change within PL0353; only keep source-correct privacy protections. No legal/factory release changes.

### Stage 3: Verification, publication

- Focused CI guard tests and workflow contract negative tests PASS; PyYAML parse; Ruff+format+mypy/compileall only for modified relevant Python, `git diff --check`. Run locked default suite on one hosted Windows Quality job **only if it can be performed without triggering 6h OCCT/OCP native rebuilds**, with actual new pass/skip counts and no proprietary fixtures. Do not recycle PL0350 2158 PASS as a newly executed test.
- Before any workflow edit, inspect trigger graph and make sure packaging workflow remains manual-only with exact run lock. No new native compile. For any installed smoke, don't inadvertently trigger retention/expiry extra runs.
- Keep work under *this task*. Codex may autonomously repair technical issues in same prompt without new task numbers. Commit implementation to private main (fast-forward, non-destructive) and publish a separate `coordination/sessions/M16-C001/PL-0353_CODEX_LOG_V02.md` as log-only commit with coverage evidence and explicit remaining exceptions. End `READY_FOR_INDEPENDENT_AUDIT` only when true hosted/default CI and scanner gates are evidenced; otherwise exact `BLOCKED_<evidence>`.
- **Do not modify root TASKS.md**, ChatGPT audit files, M17 data/accuracy acceptance, PL0354+, PL0368, rights policy, existing owner local/OwnerDev worktrees, app exe, saved installer, or any shared cache. Never run disk cleanup. No customer/public releases or uploaded sensitive artifacts. `legal_review_required=true` / `public_release_authorized=false` unchanged.

START PL-0353. Finish everything that is technically safe under this one prompt.
