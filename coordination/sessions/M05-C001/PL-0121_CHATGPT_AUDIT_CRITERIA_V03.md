# PL-0121 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0121_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve the complete V1 create/chunk/status/control/completion/error models and HTTPS/version constants.
7. Make tests/fixtures/transfer-protocol-v1-golden.json available to the Swift test target as a test resource or generated authoritative equivalent sourced mechanically from that exact file.
8. Swift tests must decode/encode and compare all golden objects: create, chunk, status, cancel, resume, completion and error. Do not retype expected values independently.
9. Add fail-closed Swift decode validation for unsupported protocol versions/protocol names for status/completion/error/control as applicable, with stable error mapping.
10. Keep Python golden round-trip tests and prove both languages derive from the same fixture/contract.
11. Tests exercise the actual production-used seam and prove the relevant restart/failure boundaries.
12. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
13. Full locked suite and relevant project/static checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
