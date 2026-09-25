# PL-0121 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0121 satisfies the frozen task scope.
6. Define a versioned PackLab Transfer Protocol V1 shared by iOS Capture and the Python/Windows receiver.
7. Protocol must transfer a finalized `.packscan` as an opaque package, never individual mutable session files.
8. Define receiver identity, protocol version negotiation, transfer ID, package capture_id, total byte size, whole-package SHA-256, chunk/range semantics, status/query, completion acknowledgement, cancellation and stable error codes.
9. Design the protocol for HTTPS/TLS transport and authenticated pairing; PL-0123 will implement the security handshake, but insecure production fallback must not be part of the contract.
10. Make retry/resume idempotent: repeated create/status/chunk requests must not duplicate or corrupt bytes.
11. Add cross-language golden fixtures/tests proving Swift/Python message field names, validation, version rejection and stable error mapping.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
