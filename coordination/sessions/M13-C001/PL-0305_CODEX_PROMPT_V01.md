# PL-0305 - Codex Work Order V01

Task: **Add dimension annotations for overall H/W/D, neck and selected features**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_dimensions.py

## Frozen scope

Implement deterministic drawing-dimension entities for overall H/W/D, neck/finish dimensions and user-selected stable Design Model/CAD features. Dimension values must come from exact Design Model/CAD numerical geometry, not screen pixels. Preserve source unit state: RELATIVE uses reconstruction_units and must not display 'mm'; METRIC_UNVERIFIED may display numerical mm with an explicit unverified marker/disclaimer. Define extension lines, arrows/text anchors and collision-safe placement metadata without baking typography into domain truth. Reject stale/missing feature references.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: overall H/W/D; neck/feature dimension; RELATIVE unit label; mm_unverified label; stale feature rejection; deterministic anchors; negative/zero impossible dimension rejection; assembly component dimension.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0306 under the M13 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
