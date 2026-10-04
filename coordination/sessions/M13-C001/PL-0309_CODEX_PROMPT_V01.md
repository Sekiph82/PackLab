# PL-0309 - Codex Work Order V01

Task: **Validate drawing dimensions against Design Model numerical values**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_PROMPT_V01.md

## Frozen scope

Implement independent numerical consistency validation between technical drawing dimension entities/section annotations and the exact source Design Model/CAD representation values. Recompute expected overall/neck/selected-feature dimensions from source numerical geometry and compare to drawing entities with an explicit software/numerical tolerance. Validate unit labels, parent revisions and title-block revision references. This is software consistency checking, not physical metrology. Reject stale drawing/source pairs, unit mismatch and dimensions derived from pixel/render measurements.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: matching known dimensions; tampered dimension value; stale model/CAD revision; unit-label mismatch; relative/mm_unverified handling; selected feature dimension; deterministic validation report; software tolerance != physical tolerance.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If this final child is green, complete the M13 master log as BATCH_COMPLETED, verify local/origin/GitHub parity and clean worktree, confirm M14 was not started, end exactly `AWAITING_MILESTONE_AUDIT`, publish the master log separately and stop.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
