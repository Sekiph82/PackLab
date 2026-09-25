# PL-0121 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0121_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve the shared golden fixture resource and successful Swift/Python round-trip tests.
7. Test unsupported protocol version/name with the correct production Swift type for each applicable model: TransferStatusMessage, TransferControlMessage, TransferCompletionAcknowledgement and TransferErrorEnvelope.
8. Do not decode completion/error/control payloads as TransferStatusMessage merely to force a throw.
9. Assert stable TransferWireError.unsupportedVersion versus malformed behavior as appropriate.
10. Keep Python negative-version/error mapping tests aligned with the same authoritative fixture/contract.
11. Tests exercise the actual production-used seam and exact failure/state boundaries.
12. Full locked suite and relevant project/static checks pass truthfully.
13. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
