# PL-0076 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and accepted M03 truth preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Add a real schema-validation test path that takes encoded PackScanPhotoMetadataDocument JSON and validates it against schemas/packscan/photo-metadata.schema.json or a mechanically generated validator derived from that schema.
7. Cover available, estimated, unavailable and not_recorded for focal length, exposure, ISO and white balance, including numeric bounds and forbidden value/unit/source combinations.
8. Keep app-only fields out of the strict wire object and preserve current ISO fail-closed mapping.
9. Fail the authoritative contract test on structural/schema drift, not only source-string drift.
10. Tests exercise the actual production-used seam/authoritative schema.
11. Validation and git diff --check are clean/truthful.
12. Log uses GitHub URLs, records exact evidence, ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are consistent.
