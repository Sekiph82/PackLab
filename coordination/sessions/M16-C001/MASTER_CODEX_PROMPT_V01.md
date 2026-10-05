# M16-C001 - CI/CD, Signing & Distribution Master Codex Prompt V01

Milestone: **M16 - CI/CD, Signing & Distribution**
Executable children: **PL-0347 through PL-0367**
Deferred gate: **PL-0368 = DEFERRED_POST_M17**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

PL-0368 post-M17 gate:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0368_CODEX_PROMPT_V01.md

Master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_CODEX_LOG_V01.md

## Start rule

1. Synchronize execution checkout non-destructively with latest `origin/main`.
2. Preserve owner-local work and unrelated checkouts.
3. Verify live root `TASKS.md` authorizes M16-C001 and actor CODEX.
4. Read:
   - M15 final audit;
   - M14 final audit;
   - dependency/license register;
   - versioning policy;
   - secrets policy;
   - this master prompt/criteria;
   - exact child prompt/criteria before every child.
5. Confirm M17+ implementation is unauthorized.
6. Confirm PL-0368 remains `DEFERRED_POST_M17`.
7. Root `TASKS.md` is ChatGPT-owned. Do not edit it.

## Frozen M16 rules

- CI permissions are least privilege.
- Fork/PR workflows never receive signing secrets.
- Caches contain only reproducible dependency/tool data, never secrets/private scans/project outputs/checkpoints/signing material.
- No private/proprietary scans, supplier attachments, production artwork, credentials, Apple certificates/profiles/private keys or owner-local data may enter the public repo/artifacts.
- New build tools/dependencies require reproducible pinning/selection and license/provenance review.
- Windows production packaging has a HARD redistribution gate for actual shipped PySide6/Qt, OCP/OCCT/OCP-proxy, Open3D/native and other bundled components.
- If redistribution license/notice inventory is incomplete, stop at PL-0350. Do not call the installer release-ready.
- Default iOS CI remains unsigned and credential-free.
- Signed IPA path is optional/protected, never required for PR success, and must scrub temporary signing material.
- Artifact names/provenance always state signed/unsigned status.
- StudioVersion, CaptureVersion and PackScanSchemaVersion remain independent domains.
- No Git tag/GitHub Release is allowed in PL-0347→PL-0367.
- PL-0368 cannot run until after M17 acceptance gates and explicit future TASKS authorization.

## Exact executable order

PL-0347 → PL-0348 → PL-0349 → PL-0350 → PL-0351 → PL-0352 → PL-0353 → PL-0354 → PL-0355 → PL-0356 → PL-0357 → PL-0358 → PL-0359 → PL-0360 → PL-0361 → PL-0362 → PL-0363 → PL-0364 → PL-0365 → PL-0366 → PL-0367.

For every child:

1. read exact prompt + criteria;
2. implement only that child and accepted predecessor seams;
3. run owning workflow/static/build tests and relevant repository regression tests;
4. run dependency/license/secrets/scope checks;
5. verify root TASKS unchanged and M17+ not started;
6. publish implementation/evidence commit(s);
7. publish distinct child-log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`;
8. verify remote visibility/parity;
9. update `coordination/sessions/M16-C001/MASTER_CODEX_LOG_V01.md`;
10. continue automatically while all mandatory gates remain green.

Do not wait for intermediate ChatGPT audits.

## Special capability behavior

### GitHub-hosted runner evidence

Where possible, workflow correctness must be proven using actual GitHub Actions runs after publication, not YAML inspection alone. Record run URLs/IDs, runner OS/Xcode/Python/uv/build tool facts and artifact names/digests.

If the current connector/execution environment cannot trigger/observe the workflow directly, publish the workflow and record the exact limitation truthfully. Do not fabricate hosted-run PASS.

### PL-0350 redistribution gate

A successfully generated EXE/installer is not enough.

Before PL-0350 can be builder-green, actual bundled files must have a reviewable redistribution inventory and required notices/license texts. If the file-level native dependency inventory cannot be closed, stop with `BATCH_STOPPED`.

### PL-0358 signed IPA

If credentials are unavailable, the signed job implementation can still be builder-green if:
- workflow guard/protected-context logic is tested statically;
- unsigned CI remains green;
- no signed IPA is falsely claimed.

A real signed IPA is not required unless credentials are actually configured, but the absence must be explicit.

### PL-0368

Do not execute. Record in the master log:

`PL-0368 = DEFERRED_POST_M17`

No tag, GitHub Release or V0.1 publication.

## Stop conditions

Stop immediately on:

- unresolved Windows redistribution/license inventory;
- secret/signing-material leakage risk;
- workflow permission escalation without necessity;
- private/proprietary data dependency;
- unreviewed build dependency;
- CI workflow that only appears green by skipping required checks;
- signed/unsigned provenance ambiguity;
- unsupported false iPhone installation claim;
- release metadata/version ambiguity;
- attempt to start PL-0368 before M17;
- locked suite/build failure not proven unrelated;
- owner-required decision;
- M17+ implementation need.

On stop:
- preserve valid completed children;
- publish exact blocker evidence/log;
- set `BATCH_STOPPED`;
- record accepted/pending frontier;
- keep PL-0368 deferred;
- end master log exactly `AWAITING_MILESTONE_AUDIT`;
- stop.

## Successful pre-M17 M16 handoff

If PL-0347 through PL-0367 are builder-green:

- master index contains all 21 executable children in exact order;
- each has implementation/evidence + distinct log-only publication;
- each child log ends `READY_FOR_INDEPENDENT_AUDIT`;
- Windows redistribution gate is closed truthfully;
- Windows/iOS artifacts and signed/unsigned provenance rules are explicit;
- release manifest/changelog/checklist/rollback are implemented;
- no Git tag/GitHub Release exists from this batch;
- PL-0368 remains `DEFERRED_POST_M17`;
- final local/origin/GitHub parity is clean;
- root TASKS unchanged by Codex;
- M17 started: NO;
- set `BATCH_COMPLETED_PRE_M17_GATE`;
- end master log exactly `AWAITING_MILESTONE_AUDIT`;
- stop for independent ChatGPT audit.
