# PL-0076 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0076 — Photo metadata schema-validation remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Cross-validate the encoded Swift photo metadata against the authoritative M02 JSON Schema/fixtures, not only Swift Codable shapes.
10. Enforce status/value/source invariants so available requires valid value/source, estimated requires an allowed estimate/value/source combination, and unavailable/not_recorded cannot carry forbidden evidence.
11. Enforce authoritative numeric bounds/types including non-negative focal length/exposure, integer ISO semantics and white-balance Kelvin minimum/maximum requirements.
12. Add schema/boundary tests for every status and invalid numeric/source combination.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
