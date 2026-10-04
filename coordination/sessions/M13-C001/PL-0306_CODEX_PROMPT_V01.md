# PL-0306 - Codex Work Order V01

Task: **Add technical drawing title block with package ID, revision, units and disclaimer**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_PROMPT_V01.md

## Frozen scope

Implement a deterministic title-block data contract for technical drawings containing package/project ID, Design Model revision, CAD representation revision, parent-authority kind, drawing revision, units/scale state, selected binding/kernel/PackLab versions, generated-view list, timestamp only as presentation metadata, and mandatory authority disclaimer. For mm_unverified, disclaimer must say numerical dimensions are unverified against physical benchmark and not mold/manufacturing approval. For RELATIVE, disclaimer must say dimensions are reconstruction-relative. Do not include private ambient paths or user machine identity.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: scan-bound and standalone title blocks; relative/mm_unverified disclaimers; deterministic core metadata; revision/version fields; privacy-safe output; no machine/user path; no certification claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0307 under the M13 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
