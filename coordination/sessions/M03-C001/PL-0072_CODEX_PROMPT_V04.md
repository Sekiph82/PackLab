# PL-0072 — Codex Remediation Work Order V04

Task: **PL-0072 — Valid image metadata fixture/integration closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M04.

Preserve all correct Batch-003 source. Fix only the remaining audit boundary.

## Mandatory remediation
1. Route accepted original stills through OriginalSourceRecord.fromSource so ImageIO extraction is part of the production persistence path.
2. Add deterministic valid JPEG/HEIF fixture coverage that proves EXIF/TIFF/unknown-safe metadata extraction and decoded pixel dimensions.
3. Test malformed/unsupported image data, declared-vs-decoded dimension mismatch, immutable master overwrite protection, and derivative path separation.
4. Do not re-encode/crop/resize original source bytes.

Tests may use injected Apple-framework drivers/fakes and conditional compilation so they are reviewable on GitHub even when Windows cannot execute Xcode. Do not claim native execution unless actually run.

Create one implementation commit and one log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
