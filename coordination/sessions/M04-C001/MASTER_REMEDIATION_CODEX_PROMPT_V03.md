# M04-BATCH-004 — Master Remediation Codex Work Order V03

Milestone: **M04 — Guided Capture & Quality Intelligence**
Purpose: **Close final M04 child PL-0109**
Authorized task: **PL-0109 only**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V03.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V03.md
Child prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V04.md
Child criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_CRITERIA_V04.md
Required child log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_LOG_V04.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md

## Authorization gate

Before material work, TASKS.md must show:
- Current Milestone: M04
- Current Sprint: M04-BATCH-004
- Current Task: M04-BATCH-004
- Current Task Status: READY
- Required Actor: CODEX
- exactly 24 M04 children checked/accepted
- PL-0109 unchecked
- M03 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M05. Never fabricate PL-0068 physical evidence.

## Mission

Execute exactly:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CODEX_PROMPT_V04.md

The production M04 architecture is already accepted except for this resume/recomputation defect. This is a surgical remediation, not a redesign.

## Mandatory outcome

After the fix:

accepted detail-pass evidence before termination
→ persisted authoritative detail-pass resume state (or deterministic canonical-record reconstruction)
→ fresh runtime restore/reconstruction
→ recomputed CompletionDiagnostics
→ additional accepted capture
→ recomputed CompletionDiagnostics still retains all previously completed detail passes.

A saved aggregate completion snapshot alone is not sufficient.

Legacy sessions without the new state and corrupt/inconsistent resume state must remain truthful and fail closed rather than manufacturing completion.

## Execution discipline

1. Read TASKS.md, this master prompt/criteria, PL-0109 V04 prompt/criteria and V03 audit.
2. Inspect current `main`.
3. Implement only PL-0109.
4. Add production-session/resume behavior tests.
5. Run focused tests.
6. Run full declared locked suite.
7. Run relevant project/static checks.
8. Run `git diff --check`.
9. Verify TASKS.md and ChatGPT audits are untouched.
10. Review privacy/signing/secrets/caches.
11. Create one implementation/evidence commit.
12. Publish PL-0109 child log in a separate log-only commit.
13. Verify remote visibility.
14. Publish the master log in a final evidence-only commit.

## STOP conditions

Stop if:
- authorization/repository safety fails;
- the fix requires M05/later-milestone implementation;
- a genuine owner/ADR decision is required;
- physical evidence would need fabrication;
- protected files would need Codex edits;
- privacy/signing risk appears;
- full declared suite cannot run truthfully.

On stop, publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

Verify:
- all 24 already accepted M04 children remain unregressed;
- M03 remains accepted;
- PL-0068 remains OWNER_REQUIRED;
- no M05 work;
- full declared locked suite passes;
- relevant project/static checks pass;
- `git diff --check` passes;
- TASKS.md/ChatGPT audits untouched;
- privacy/signing/cache review clean.

Native Swift/Xcode/iPhone validation may be claimed only if actually executed.

## User-facing link policy

Every user-facing repository reference must be a full GitHub URL. Never output local checkout/file paths.

## Final handoff

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_LOG_V03.md

The master log must link the V04 child prompt/criteria/audit/log, exact implementation/log commits, validation results and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
