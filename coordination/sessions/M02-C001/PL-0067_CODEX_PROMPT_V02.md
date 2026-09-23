# PL-0067 — Codex Work Order V02

Task: **PL-0067 — Synthetic calibration ground-truth reconciliation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_RESUME_REMEDIATION_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the PL-0067 V01 prompt/criteria, the completed M02 remediation audit above, this V02 prompt and its criteria.

TASKS.md must show:
- Current Milestone: M02
- Current Task: PL-0067
- Current Task Status: READY
- Required Actor: CODEX
- Next Task/Action pointing to this V02 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require a safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md or ChatGPT audit artifacts. Do not start PL-0068 or M03.

## Mission

Reconcile and complete PL-0067 against the now-audited post-remediation calibration contracts. Reuse correct existing synthetic-ground-truth work where valid; do not rewrite working code merely for churn.

The current repository already contains partial synthetic-ground-truth coverage. Treat it as starting evidence, not automatic closure. In particular, prove the actual marker-detection contract rather than satisfying detection coverage only by directly constructing post-detection `MarkerObservation` objects.

## Authorized primary scope

- `tests/calibration/**`
- `core/src/packlab_core/calibration/**`
- `docs/calibration/**`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory requirements

1. Build/retain deterministic synthetic cases with explicit marker geometry, ground-truth dimensions, units, coordinate conventions and reproducible generator/provenance parameters.
2. Exercise the actual marker-detection contract with synthetic/public data. Do not count direct construction of `MarkerObservation` as detector coverage.
3. Exercise detection -> scale -> confidence -> profile compatibility/reuse behavior without private images.
4. Cover ideal, noisy, partial, degenerate and inconsistent cases with explicit expected outcomes/error bounds.
5. Add sensitivity-bearing perturbations for scale math, units, corner ordering and marker geometry.
6. Preserve PL-0063 degenerate-geometry rejection and PL-0064 residual/spread hard-gate semantics.
7. Preserve PL-0066 fail-closed provenance: synthetic/public evidence must remain non-reusable as owner/native/physical calibration evidence unless genuine owner-controlled evidence exists. Never fabricate such evidence to make a test pass.
8. Run focused positive/negative/boundary tests plus the relevant full PackScan/calibration regression.
9. If the current implementation already satisfies a requirement, prove it with executable evidence rather than making cosmetic edits.

## Validation

Run:
- relevant focused pytest for PL-0067;
- full `tests/calibration`;
- full `tests/packscan tests/calibration`;
- Ruff format/check on touched Python;
- mypy on touched Python when available;
- `git diff --check`;
- `git diff -- TASKS.md`;
- exact changed-file review;
- privacy/secrets/signing scan over touched files.

Tests must be behavior/sensitivity-bearing. Do not substitute string-presence assertions where geometry, detector, numerical, schema or relationship behavior is required.

Do not claim native iPhone, physical ruler/caliper, printer, camera or owner-benchmark evidence unless it actually exists.

## Handoff

Commit/push authorized implementation/evidence, then publish:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CODEX_LOG_V02.md

The log must record synchronized start, implementation commit, exact files changed, requirement mapping, commands/results, any failures/fixes, platform/evidence limitations, privacy review and remote visibility.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not self-audit and do not start PL-0068.
