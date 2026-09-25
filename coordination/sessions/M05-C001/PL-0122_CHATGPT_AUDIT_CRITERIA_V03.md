# PL-0122 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0122_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve PairingOffer, reconnect identity store and PairingCoordinator concepts.
7. Make the real Send-to-PackLab workflow support manual pairing without requiring a pre-injected PairingOffer that is unavailable in the UI. Provide a truthful offer acquisition/input mechanism containing receiver host/port/ID/fingerprint plus short-lived code, or a receiver-discovery mechanism explicitly within M05 scope.
8. Do not persist the one-time pairing code; persist only receiver ID, host, port and TLS fingerprint.
9. Do not present/start PairingQRScannerController until production camera ownership is actually acquired for pairing.
10. Bind pairing scanner ownership to the real production camera/NextLevel lifecycle: stop/release production capture before QR AVCaptureSession starts, reject scan if ownership cannot be acquired, and restore/restart capture ownership cleanly when scanning ends/cancels/fails.
11. Add Swift tests for valid manual and QR pairing, expired offer, wrong version, malformed payload, wrong receiver, reconnect persistence without code, acquisition failure, no concurrent production camera/scanner session and hand-back.
12. Tests exercise the actual production-used seam and prove the relevant restart/failure boundaries.
13. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
14. Full locked suite and relevant project/static checks pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
