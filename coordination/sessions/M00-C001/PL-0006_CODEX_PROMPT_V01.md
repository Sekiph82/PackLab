# PL-0006 - Codex Child Work Order V01

Task: **PL-0006 - Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema**

Repository: https://github.com/Sekiph82/PackLab
Master work order:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md

This child prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_PROMPT_V01.md

Frozen child criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CHATGPT_AUDIT_CRITERIA_V01.md

Required child log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_LOG_V01.md

## Authority

Read before work:

https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md

Root TASKS.md must still authorize M00-BATCH-001 and Required Actor CODEX. Do not edit TASKS.md.

## Objective

Strictly revalidate the existing canonical artifact at:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md

Do not change it unless a genuine substantive defect is found.

## Mandatory content

1. Preserve three independent version domains: StudioVersion, CaptureVersion, and PackScanSchemaVersion.
2. Preserve SemVer-style MAJOR.MINOR.PATCH rules for Studio and Capture.
3. Preserve explicit MAJOR/MINOR/PATCH compatibility semantics for PackScan schema.
4. Preserve the full compatibility matrix for old/new Studio, Capture, and schema combinations.
5. Preserve reader/writer rules that reject unsupported future MAJOR versions and forbid silent reinterpretation of units, coordinate frames, checksum rules, orientation, calibration, or required file meaning.
6. Preserve explicit, versioned, non-destructive migration rules with source/target versions and visible lossy-migration handling.
7. Preserve future application-to-schema compatibility declarations and PL-0363/PL-0364 ownership of release numbering/manifests.
8. Preserve immutable .packscan evidence, millimetres as canonical engineering units unless changed by audited ADR, and Scan Mesh/Scan Master/Design Model separation.
9. Do not rewrite VERSIONING_POLICY.md unless a genuine substantive defect is found. If unchanged, prove exact unchanged status.
10. Revalidate the accepted V01 substantive policy against current repository truth; the previous C001 synchronization defect is historical evidence, not a reason to manufacture a content change.

## Scope rules

- Work only on PL-0006.
- Do not start the next child until this child implementation validations are green and its log is pushed.
- Do not implement M01.
- Do not modify root TASKS.md.
- Do not create ChatGPT audit files.
- Do not change prior prompt/log/audit history.
- Do not commit secrets, private Kenya scans, confidential supplier assets, signing private material, credentials, caches or local environments.
- If an architecture contradiction requires an ADR outside this child scope, stop the entire batch with ADR_REQUIRED.
- If an owner decision or unavailable dependency blocks this child, stop the entire batch and record the blocker.

## Validation

Run and record:

```powershell
git diff --check
git diff -- TASKS.md
git status --short --branch
```

Perform explicit content checks covering every Mandatory content item above.

Perform an exact changed-file review and protected-file review.

If docs/architecture/VERSIONING_POLICY.md remains unchanged, prove exact unchanged status against this child's synchronized starting commit.

## Authorized implementation/evidence

Existing artifact: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/VERSIONING_POLICY.md

Default expected result is no policy-file change if no substantive defect is found.

The matching child log path is:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_LOG_V01.md

## Child log contract

The child log must record:

- PL-0006;
- full prompt URL;
- full criteria URL;
- child starting commit;
- implementation/evidence commit;
- files read;
- files changed;
- each required validation with expected result, failure condition and actual result;
- failures/fixes;
- scope review;
- privacy/security review;
- push/remote visibility evidence;
- known limitations;
- `READY_FOR_INDEPENDENT_AUDIT`.

Do not predeclare the future log-containing commit SHA.

## Commit / continue

Commit and push this child's implementation/evidence first, then publish the child log as a separate log-only commit where practical.

After remote verification, continue to the next child listed in the master prompt only if this child is validation-green and no STOP condition exists.

Codex does not assign AUDITED_PASS.
