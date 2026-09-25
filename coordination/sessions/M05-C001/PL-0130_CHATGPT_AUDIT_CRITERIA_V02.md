# PL-0130 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0130_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve QuarantineStore content-addressed package retention and atomic event history.
7. Add genuine PackScan fixtures for unsupported future schema, internal manifest/checksum mismatch, unsafe/malicious ZIP path/name, corrupt ZIP and repeated quarantine.
8. Prove package-provided filenames/path fragments never influence quarantine destination names.
9. Prove every quarantined case creates no normal raw/import/extraction artifacts and retains only redacted structured diagnostics.
10. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
11. Invalid/incomplete/untrusted data never reaches normal import authority.
12. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
13. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
14. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
