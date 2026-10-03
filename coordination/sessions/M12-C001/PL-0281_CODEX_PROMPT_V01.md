# PL-0281 - Codex Work Order V01

Task: **Allow swapping trigger/pump variants without modifying bottle geometry**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read M12 master, M11 audit, M09 physical deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0277_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0278_CODEX_PROMPT_V01.md

## Frozen scope

Implement explicit trigger/pump variant replacement in the assembly graph. Swap must create a new assembly revision, preserve bottle/body and Scan Master parents byte-for-byte, validate attachment compatibility and leave previous assembly history intact. Incompatible variants fail closed; no silent bottle adaptation.

## Authority rules

Exact captured Scan Master remains immutable where present. Design Model/assembly/library/flexible-pack authorities remain explicitly separated. `METRIC_UNVERIFIED` stays unverified. Flexible-pack geometry is design/visualization geometry, not mold-grade. No M13 CAD/BREP/STEP implementation. No private/raw data or unlicensed library asset may be silently imported.

## Required tests/evidence

At minimum cover: compatible swap, incompatible attachment, stale variant, body revision unchanged, old assembly retained, deterministic new revision, undo/redo/history compatibility.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0282 under the M12 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
