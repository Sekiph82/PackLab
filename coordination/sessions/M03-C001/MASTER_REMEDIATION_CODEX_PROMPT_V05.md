# M03-BATCH-006 — Master Remediation Codex Work Order V05

Milestone: **M03 — iOS Capture Foundation**
Purpose: **Close the final three M03 camera-control audit gaps**
Authorized tasks: **PL-0073, PL-0074, PL-0075**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V04.md
This master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V05.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V05.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V05.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M03
- Current Task: M03-BATCH-006
- Current Task Status: READY
- Required Actor: CODEX
- exactly 22 M03 children accepted
- PL-0073, PL-0074 and PL-0075 unchecked
- PL-0068 still unchecked / OWNER_REQUIRED
- Next Task/Action pointing to this master V05 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work run:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only when safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit root TASKS.md or ChatGPT audit artifacts. Never start M04. Never fabricate PL-0068 evidence.

## Accepted M03 children that must not regress

Every M03 child except PL-0073, PL-0074 and PL-0075 is already independently accepted. Preserve all of them.

## Batch objective

The production camera architecture is already correct enough to keep:
- deterministic selected rear main-wide device;
- one camera configuration coordinator;
- one runtime control bridge;
- focus/exposure/white-balance production composition;
- accepted-photo metadata persistence;
- shared recovery owner;
- health-gated still capture.

The only remaining problem is **behavior evidence at the physical AVFoundation adapter seam**.

Do not add another camera-control architecture.

Instead, extract the smallest **production-used injectable camera-device-control driver/seam** under the current adapter/composition code. The real AVCaptureDevice wrapper must use this seam, and tests must drive the same seam with deterministic fakes.

## Ordered children

Execute exactly:

1. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0073_CODEX_PROMPT_V06.md
2. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0074_CODEX_PROMPT_V06.md
3. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0075_CODEX_PROMPT_V06.md

For each child:
- read its previous V05 audit;
- implement only the frozen V06 remediation;
- preserve all existing production behavior;
- add behavior-bearing tests against the production-used injected device-control seam;
- run focused + relevant M03 regression/static/project checks;
- run `git diff --check`;
- prove TASKS.md and ChatGPT audits are untouched;
- create a distinct implementation commit;
- publish the child V06 log in a separate log-only commit;
- verify remote visibility before continuing.

## Required integrated proof

By the end of the batch, tests must prove through the production-used device-control seam:

### Focus
- wrong-device rejection;
- continuous autofocus start;
- adjusting focus state;
- observed stable focus;
- lock-before-stable rejection;
- lock-after-stable success;
- runtime UI propagation.

### Exposure
- wrong-device rejection;
- target-bias clamping;
- metering state;
- lock behavior;
- serialized device configuration;
- runtime UI propagation;
- persisted exposure/ISO evidence.

### White balance
- wrong-device rejection;
- continuous-auto start;
- adjusting white-balance state;
- stabilization;
- lock-before-stable rejection;
- lock-after-stable success;
- observed temperature handling;
- runtime UI propagation;
- persisted WB evidence.

Injected driver values are deterministic **test fixtures**, never physical-device evidence.

## User-facing link policy

Codex may use local checkout paths internally, but every user-facing repository reference must be a full GitHub URL.

Never output:
- `C:\Users\...`
- `C:/Users/...`
- `file://...`
- Markdown links targeting local paths.

Final handoff must link:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V05.md

## STOP conditions

Stop if:
- authorization/repository safety fails;
- a finding requires M04 or an owner/ADR decision;
- protected files would need editing;
- a privacy/signing risk appears;
- relevant regression cannot be repaired inside these three tasks.

If stopped, publish truthful evidence and end the master log `BATCH_STOPPED`.

## Final validation

After all three:
- verify the 22 previously accepted M03 children remain unregressed;
- verify PL-0068 remains OWNER_REQUIRED;
- verify no M04 work;
- run all repository-supported relevant M03 regression/project/static validation;
- run `git diff --check`;
- verify TASKS.md / ChatGPT audits untouched;
- verify distinct implementation + log commits for all three children;
- review privacy/signing/cache scope.

Publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_LOG_V05.md

The master log must use full GitHub URLs and index all three children with prompt, criteria, audit, implementation commit, log commit, validation and limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
