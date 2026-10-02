# PL-0230 - Codex Work Order V01

Task: **Implement optional bounded hole filling as a non-destructive revision**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M10-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CODEX_LOG_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M10-C001 / ordered PL-0225 through PL-0240 batch / READY / CODEX. Re-read the M10 master prompt, accepted M09 partial audit, owner deferral decision, repository rules and this child criteria. Fetch and fast-forward only when safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## Frozen scope

Implement optional geometric hole filling only from PL-0229-reported eligible holes and only under explicit maximum perimeter/area/vertex-count safeguards. Filled faces are derived repair geometry and must be labeled as such in provenance. Preserve before/after revisions, never overwrite captured geometry, and retain unresolved/large holes as limitations. No AI/generated completion or hidden surface invention beyond the bounded local repair rule.

## Deferred physical-validation rules

PL-0220 through PL-0224 remain deferred, not passed. M10 must preserve inherited scale state and provenance. A METRIC_UNVERIFIED parent stays unverified. No output may claim physical accuracy, mold readiness or manufacturing suitability merely because M10 geometry cleanup succeeds.

RAW_CAPTURE, reconstruction and original OBJECT_CAPTURE_GEOMETRY remain immutable. AI_VISUAL_REFERENCE/generated geometry cannot enter Scan Master ancestry.

## Required tests/evidence

At minimum cover: small eligible hole fill, oversized hole rejection, multiple holes mixed eligibility, derived-repair face provenance, before/after digests, parent immutability, deterministic topology.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If green and no real stop condition exists, continue directly to PL-0231 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or master stop condition. M11 is unauthorized.
