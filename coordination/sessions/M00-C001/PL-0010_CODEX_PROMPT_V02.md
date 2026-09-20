# PL-0010 — Codex Remediation Work Order V02

Task: **PL-0010 — Create project risk register with technical, licensing, capture-quality, signing and hardware risks**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

Current tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

V01 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CHATGPT_AUDIT_V01.md

V01 artifact:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/RISK_REGISTER.md

This V02 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_PROMPT_V02.md

Matching criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V02.md

## Mission

Correct the Related PL task IDs in `docs/architecture/RISK_REGISTER.md`.

The V01 audit found multiple well-formed but semantically unrelated PL task links. Preserve the accepted risk descriptions, likelihood/impact judgments, evidence/status boundaries, mitigations, contingencies, and ownership unless a link correction requires a minimal wording adjustment.

## Required method

1. Read root `TASKS.md` fully enough to verify every referenced PL task by its actual task text.
2. Review every row in `RISK_REGISTER.md`.
3. For every `Related PL task IDs` entry, verify that each referenced task actually owns or materially contributes to the risk's mitigation, evidence, implementation, validation, or contingency.
4. Remove unrelated task IDs.
5. Add the most directly relevant task IDs where needed.
6. Prefer a small accurate set over a long speculative set.
7. Do not invent new task IDs.
8. Do not change any checkbox or lifecycle state in `TASKS.md`.

Examples of V01 defects that must be corrected:
- capture-quality risk linked to Python/Ruff tasks;
- calibration risk linked to Python workspace/iOS permission tasks;
- ARKit runtime risk linked to pytest/logging tasks;
- dependency/licensing risks linked to the object-mask task;
- supplier/private Kenya provenance linked to Ruff;
- reconstruction reliability linked to unrelated simulator/Python tasks.

These examples are not an exhaustive correction list. Validate all rows.

## Full regression revalidation

After correcting the links, revalidate the entire PL-0010 contract:

- stable risk IDs;
- required table fields;
- glossy/transparent/low-texture photogrammetry risk;
- scale/calibration and physical-evidence distinction;
- iPhone 16 Standard no-LiDAR and ARKit variability;
- host GPU/CUDA uncertainty without treating AdapterRAM as dedicated VRAM;
- dependency/packaging/license risk across COLMAP/OpenMVS/Open3D/OpenCascade/Blender/PySide6;
- OpenMVS AGPL attention without legal certification;
- Apple signing/provisioning/free-first distribution uncertainty;
- public-repository privacy/security leakage;
- schema/app compatibility and migration;
- supplier/private Kenya provenance;
- disk/storage/long-running reconstruction failure and reproducibility;
- distinction between current evidence, hypotheses, planned mitigations, and implemented controls.

## Scope

Authorized product file:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/RISK_REGISTER.md

Authorized log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V02.md

Do not edit:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Do not modify accepted PL-0006..PL-0009 or PL-0011..PL-0018 artifacts.

Do not start M01.

## Validation

Run and record:

```powershell
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
git diff --check
git diff -- TASKS.md
```

Before material work, require synchronized `0 0` and no unexpected tracked changes.

Perform:
- an exact diff review of `RISK_REGISTER.md`;
- a row-by-row semantic verification of every referenced PL ID against root `TASKS.md`;
- a protected-file review;
- a privacy/security review;
- a full PL-0010 regression review.

## Log

Create:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V02.md

Record:
- prompt and criteria full URLs;
- synchronized starting commit;
- implementation commit;
- exact old -> new Related PL task-ID mapping for every changed risk row;
- evidence from TASKS.md showing why each replacement is related;
- all validation commands and results;
- failures/fixes;
- scope/privacy review;
- push/remote visibility evidence;
- limitations;
- `AWAITING_AUDIT`.

Do not self-audit. Do not predeclare the future log-containing commit SHA.

## Final response

Return only:

`PL-0010 V02`

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_LOG_V02.md

`AWAITING_AUDIT`

Then stop.
