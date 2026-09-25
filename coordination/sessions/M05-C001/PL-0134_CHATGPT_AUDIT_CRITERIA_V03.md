# PL-0134 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0134_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve the corrected missing-image fixture and all existing Windows ingest/quarantine assertions.
7. Replace the static Swift-source-string 'integration' check as milestone evidence with an executable cross-language transport contract harness.
8. The harness must exercise the same wire serialization, routes, transfer-ID persistence/resume semantics and completion validation used by URLSessionTransferClient against the real PackLabReceiver HTTPS endpoint. Prefer an Apple-capable Swift integration test when available; otherwise create a mechanically shared transport script/fixture generated from the Swift/Python authoritative protocol contract, not a source-text grep.
9. Exercise network pairing/auth, certificate pin identity, partial upload, sender same-ID restart/resume, receiver restart, cancel/retry, verified completion and exactly-once raw/index/report ingest in one coherent deterministic test chain.
10. Retain corrupt ZIP, bad manifest, internal checksum mismatch, future schema, unsafe path and isolated missing-declared-image quarantine coverage.
11. Static inspection may supplement but must not substitute for executable transport behavior.
12. Tests exercise actual production-used behavior and exact failure/restart boundaries.
13. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
14. Full locked suite and relevant project/static checks pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
