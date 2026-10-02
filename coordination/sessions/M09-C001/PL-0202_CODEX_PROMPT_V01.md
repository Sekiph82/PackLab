# PL-0202 - Codex Work Order V01

Task: **Detect calibration markers and bind them to reconstructed cameras**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/marker-detection.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/marker-policy.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/calibration/marker_detection.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/object_mask_lifting.py

## Frozen scope

Reuse the accepted PackLab marker detector and marker policy. Create a deterministic observation-to-camera association contract keyed by source image asset ID/digest and camera solution revision. Preserve ordered image-pixel corners and detector provenance. Reject missing, duplicate, stale, dimension-mismatched or ambiguous image/camera bindings. This child detects/associates only: it does not infer physical scale or promote metric authority.

Preserve RAW_CAPTURE and accepted M08 artifacts. M09 may establish measurement/calibration evidence but must never fabricate physical evidence, owner measurements, printer verification or METRIC_VERIFIED state. AI_VISUAL_REFERENCE remains non-authoritative.

## Required tests/evidence

At minimum cover: synthetic marker association, duplicate/missing camera identity, source digest mismatch, corner/coordinate preservation, deterministic serialization, unavailable OpenCV, source immutability.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless the child explicitly requires owner-controlled physical evidence.

Use a separate implementation/evidence commit followed by a separate child-log-only commit. The log records exact commands/results, changed files, provenance/authority decisions and limitations, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If all frozen gates are green and no real stop condition exists, continue directly to PL-0203 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition.
