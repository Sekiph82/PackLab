# PL-0072 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED and PL-0070 remains accepted.
3. TASKS.md and ChatGPT audits are untouched by Codex; M04 is not started.
4. Prior Batch-003 passing behavior is preserved.
5. Previous audit PL-0072_CHATGPT_AUDIT_V03.md is fully addressed.
6. Route accepted original stills through OriginalSourceRecord.fromSource so ImageIO extraction is part of the production persistence path.
7. Add deterministic valid JPEG/HEIF fixture coverage that proves EXIF/TIFF/unknown-safe metadata extraction and decoded pixel dimensions.
8. Test malformed/unsupported image data, declared-vs-decoded dimension mismatch, immutable master overwrite protection, and derivative path separation.
9. Do not re-encode/crop/resize original source bytes.
10. Behavior tests drive the actual production seam or an injected driver used by that seam, not a disconnected helper.
11. Relevant regressions/project checks and git diff --check are truthful and clean.
12. Child log records exact commits/files/results/limitations and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final main source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
