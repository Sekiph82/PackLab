# PL-0068 — Codex Work Order V02

Task: **PL-0068 — First physical calibration benchmark preparation / owner handoff**

Repository: https://github.com/Sekiph82/PackLab
Previous task audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0067_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, PL-0068 V01 prompt/criteria, this V02 prompt/criteria, and these accepted calibration contracts:
- docs/calibration/mat-assets.md
- docs/calibration/pre-use-verification.md
- docs/calibration/verification-record-template.md
- docs/calibration/iphone-main-camera-calibration.md
- docs/calibration/scale-estimation.md
- docs/calibration/confidence-thresholds.md
- docs/calibration/profile-storage.md

TASKS.md must show:
- Current Milestone: M02
- Current Task: PL-0068
- Current Task Status: READY
- Required Actor: CODEX
- Next Task/Action pointing to this V02 prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronization. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md or ChatGPT audit artifacts. Do not start M03.

## Mission

Prepare the repository for the first real physical calibration benchmark without fabricating physical evidence.

The existing repository already has printable mats, printed-mat verification procedure/template, scale/confidence/profile contracts and an iPhone 16 Standard main-camera calibration procedure. Reuse them. Add only what is missing for a complete physical benchmark record and owner execution handoff.

## Authorized primary scope

- `docs/calibration/benchmarks/**`
- `tests/calibration/**`
- `assets/calibration/**`

Minimal adjacent calibration files are allowed only when technically necessary and must be justified in the log.

## Mandatory preparation

1. Create a concise physical-benchmark procedure that links the accepted printed-mat verification record to the benchmark capture/session.
2. Create a benchmark record/template containing at least:
   - record/version/status/provenance;
   - exact mat asset and accepted verification-record reference;
   - device model, lens, camera position, resolution, orientation, zoom and focus;
   - capture app/policy/model versions;
   - capture conditions and sample counts;
   - every accepted and rejected sample;
   - known dimension in mm;
   - estimated dimension in mm;
   - signed error in mm;
   - absolute error in mm;
   - percentage error;
   - aggregate statistics;
   - explicit owner-controlled evidence references.
3. State formulas unambiguously. Do not hide rejected samples from the record.
4. Add deterministic validation/tests only if they materially protect the record contract. Avoid unnecessary framework work.
5. Preserve the existing PL-0060/61/65 contracts and PL-0066 provenance requirements.
6. Do not invent an acceptance threshold from absent physical data. If a provisional threshold already exists elsewhere, cite/reuse it exactly and label it provisional.
7. Do not add private scans/photos to public Git. Owner evidence may be referenced by safe IDs/metadata; private raw evidence stays outside public Git unless the owner explicitly provides a redistributable artifact.
8. Do not fabricate measurements, iPhone execution, printer output, caliper/ruler readings or benchmark statistics.

## Validation

Run relevant docs/tests plus any new focused tests, relevant calibration regression if code/tests are touched, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

## Handoff rule

If genuine owner-controlled physical benchmark evidence is not already available, that is expected.

In that case:
- finish only the preparation artifacts;
- publish PL-0068_CODEX_LOG_V02.md;
- list exactly what the owner must physically do/measure next;
- state clearly that PL-0068 is not complete;
- end the log exactly with:

`OWNER_REQUIRED`

Do not self-audit and do not start M03.
