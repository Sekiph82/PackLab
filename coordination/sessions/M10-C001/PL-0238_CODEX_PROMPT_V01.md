# PL-0238 - Codex Work Order V01

Task: **Add Promote to Scan Master action with hard authority gate**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M10-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CODEX_LOG_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M10-C001 / ordered PL-0225 through PL-0240 batch / READY / CODEX. Re-read the M10 master prompt, accepted M09 partial audit, owner deferral decision, repository rules and this child criteria. Fetch and fast-forward only when safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Frozen scope

Implement the Windows Studio/application action that requests domain promotion to Scan Master with explicit actor/reason/audit metadata. The UI/action must delegate eligibility and revision truth to the core Scan Master service. Hard reject generated/AI_VISUAL_REFERENCE, preview proxy as selected authority, incomplete provenance, stale parents or unauthorized authority classes. Promotion before physical validation must visibly retain DEFERRED_OWNER_VALIDATION, inherited scale state and mold_use_authorized=false.

## Deferred physical-validation rules

PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed. Preserve inherited scale state and scale provenance. A METRIC_UNVERIFIED parent stays unverified. Scan Master authority is captured-geometry workflow authority, not proof of physical accuracy or mold suitability.

RAW_CAPTURE, reconstruction and original OBJECT_CAPTURE_GEOMETRY remain immutable. AI_VISUAL_REFERENCE/generated geometry cannot enter Scan Master ancestry.

## Required tests/evidence

At minimum cover: eligible promotion, AI/generated/proxy rejection, incomplete/stale provenance, actor/reason audit metadata, UI delegation, reopen persistence, deferred-validation visibility.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If green and no real stop condition exists, continue directly to PL-0239 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or master stop condition. M11 is unauthorized.
