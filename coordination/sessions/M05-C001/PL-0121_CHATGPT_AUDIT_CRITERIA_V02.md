# PL-0121 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0121_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve the existing protocol name/version/create/chunk fields and HTTPS-only contract.
7. Define matching Swift and Python wire models for status/query, cancellation/resume, completion acknowledgement and stable error response envelopes.
8. Define idempotent retry/resume semantics explicitly in the shared protocol contract, including authoritative confirmed offset and duplicate request behavior.
9. Create authoritative golden fixtures consumed by both Swift and Python tests for create, chunk, status, cancel/resume, completion and errors, including version rejection and stable error-code mapping.
10. Tests exercise the actual production-used seam rather than only a disconnected policy/helper.
11. Invalid/incomplete/untrusted data never reaches normal import authority.
12. Security/privacy/secret claims are truthful and no secrets/private keys enter Git/logs/package data.
13. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
14. Child log uses full GitHub URLs, records exact commits/results/limitations, and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
