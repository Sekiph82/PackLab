# M05-BATCH-001 — Master ChatGPT Audit Criteria V01

Milestone: **M05 — Transfer & Ingest**
Children: **PL-0119 through PL-0134**

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-001 / READY / CODEX before material work.
2. M03/M04 remain accepted and unregressed.
3. PL-0068 remains unchecked / OWNER_REQUIRED.
4. Child set/order is exactly PL-0119..PL-0134.
5. Every child has a frozen V01 prompt/criteria before implementation.
6. Codex never edits TASKS.md or ChatGPT audit artifacts.
7. No M06 implementation starts.
8. Existing PackScan writer/validator/session authority is reused; no parallel mutable export format is introduced.
9. PL-0119 finalization is checksum-complete and atomically published with no partial-success state.
10. PL-0120 shares only finalized .packscan packages through the system share-sheet boundary.
11. PL-0121 defines one stable, cross-language, versioned transfer protocol.
12. PL-0122 pairing is receiver-specific, short-lived/revocable and supports manual code plus QR workflow.
13. PL-0123 production local transfer is encrypted/authenticated using standard TLS/platform cryptography and receiver identity pinning; no custom crypto or insecure fallback.
14. PL-0124 resume is persisted/idempotent and survives sender/receiver interruption without byte corruption.
15. PL-0125 receiver verifies the whole-package digest before publication/acknowledgement.
16. PL-0126 progress comes from confirmed bytes and cancel/retry preserves finalized source evidence.
17. PL-0127 manual Windows ingest entry points for drop/file-selection converge on one import service without starting M06 shell.
18. PL-0128 paired receiver feeds only authenticated, complete, checksum-verified packages to Capture Inbox/ingest.
19. PL-0129 validates schema/version/checksums/paths before extraction.
20. PL-0130 corrupt/unsupported input is quarantined without partial normal import.
21. PL-0131 valid input receives immutable raw evidence storage with digest provenance and no silent overwrite.
22. PL-0132 import report is structured, deterministic, privacy-safe and based on authoritative validated data.
23. PL-0133 dedupe/conflict behavior is atomic and fail-closed for capture ID/digest ambiguity.
24. PL-0134 end-to-end tests cover interrupted/resumed transfer, corrupt ZIP, missing image/photo evidence, bad manifest, checksum failure, unsupported version and unsafe path.
25. Invalid/incomplete/untrusted data never enters normal import authority.
26. Secrets/private keys/session credentials never enter Git, package data, QR payloads beyond permitted short-lived pairing material, or logs.
27. Any new runtime dependency is declared/locked/reproducible and does not weaken security.
28. Every child has a distinct implementation/evidence commit and log-only commit ending READY_FOR_INDEPENDENT_AUDIT.
29. Full locked suite and relevant project/static/network/ingest checks pass truthfully.
30. git diff --check/protected-file/privacy/signing checks are clean.
31. Native/physical/LAN/AirDrop claims are truthful.
32. User-facing repository links are full GitHub URLs only.
33. Master log accurately indexes all 16 children and ends AWAITING_MILESTONE_AUDIT.
34. M05 closes only after independent ChatGPT child-by-child audit.

PL-0068 may remain OWNER_REQUIRED under the existing owner-authorized exception.
