# PL-0232 - Codex Work Order V01

Task: **Compute M10 geometric statistics**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M10-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CODEX_LOG_V01.md

Owner physical-validation deferral:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M10-C001 / ordered PL-0225 through PL-0240 batch / READY / CODEX. Re-read the M10 master prompt, accepted M09 partial audit, owner deferral decision, repository rules and this child criteria. Fetch and fast-forward only when safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## Frozen scope

Implement deterministic geometry statistics needed by later fitting/review: point/vertex/face counts, bounds, surface/edge statistics where applicable, connected-component summary, hole summary linkage, density/spacing proxies and any explicitly documented topology indicators. Metrics must state units/assumptions and remain diagnostics, not physical-accuracy claims. Bind exact geometry revision and scale state.

## Deferred physical-validation rules

PL-0220 through PL-0224 remain deferred, not passed. M10 must preserve inherited scale state and provenance. A METRIC_UNVERIFIED parent stays unverified. No output may claim physical accuracy, mold readiness or manufacturing suitability merely because M10 geometry cleanup succeeds.

RAW_CAPTURE, reconstruction and original OBJECT_CAPTURE_GEOMETRY remain immutable. AI_VISUAL_REFERENCE/generated geometry cannot enter Scan Master ancestry.

## Required tests/evidence

At minimum cover: point-cloud and mesh stats, empty/degenerate rejection, relative/mm_unverified labeling, deterministic metrics, linkage to component/hole reports, no physical accuracy claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If green and no real stop condition exists, continue directly to PL-0233 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or master stop condition. M11 is unauthorized.
