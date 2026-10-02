# PL-0233 - Codex Work Order V01

Task: **Create Scan Master asset with captured-evidence-only ancestry**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M10-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CODEX_LOG_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M10-C001 / ordered PL-0225 through PL-0240 batch / READY / CODEX. Re-read the M10 master prompt, accepted M09 partial audit, owner deferral decision, repository rules and this child criteria. Fetch and fast-forward only when safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Frozen scope

Implement the domain Scan Master asset/revision contract and eligibility gate exactly against PL-0233 authority rules. Only captured-evidence ancestry may promote: RAW_CAPTURE -> RECONSTRUCTION_OBSERVATION -> OBJECT_CAPTURE_GEOMETRY -> M09 scale/alignment -> M10 conservative cleanup. Generated/AI_VISUAL_REFERENCE and preview proxies are ineligible. Persist complete promotion manifest, source/output digests, cleanup operations, hole report, scale provenance and alignment. Because physical validation is deferred, inherited scale state must remain unchanged and the Scan Master must explicitly record physical_accuracy_validation_status=DEFERRED_OWNER_VALIDATION and mold_use_authorized=false. Promotion never overwrites source/reconstruction/object geometry.

## Deferred physical-validation rules

PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed. Preserve inherited scale state and scale provenance. A METRIC_UNVERIFIED parent stays unverified. Scan Master authority is captured-geometry workflow authority, not proof of physical accuracy or mold suitability.

RAW_CAPTURE, reconstruction and original OBJECT_CAPTURE_GEOMETRY remain immutable. AI_VISUAL_REFERENCE/generated geometry cannot enter Scan Master ancestry.

## Required tests/evidence

At minimum cover: eligible captured ancestry, generated/AI rejection, preview proxy rejection, complete manifest, source/output digest, cleanup/hole linkage, immutable parents, deferred physical-validation flag, scale state preservation, deterministic revision identity.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If green and no real stop condition exists, continue directly to PL-0234 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or master stop condition. M11 is unauthorized.
