# PL-0134 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

The missing-image fixture is now correctly isolated: it keeps the control files and checksums structure while declaring one image that is absent, and the receiver quarantines it as missing_declared_entry. The Windows integration assertions remain useful. But the core V02 requirement is still unmet: the test suite does not drive the authoritative iOS/cross-language sender into the real HTTPS receiver. tests/transfer/test_cross_language_integration_contract.py only reads Swift source text and checks that route/model strings exist. tests/transfer/test_m05_integration.py still calls PackLabReceiver methods directly with token_authenticated=True. The separate Python loopback test uses urllib, not the production Swift/iOS client seam. Thus pairing + pinning + authenticated sender + partial upload + sender restart/resume + receiver restart + exactly-once ingest are not proven as one cross-language production chain.

## Required remediation

Create an executable transport-level contract harness that drives the same request/response serialization and state machine used by URLSessionTransferClient against the real HTTPS receiver, or run an Apple-capable Swift integration test against that receiver. It must cover pairing/pinning, partial transfer, persisted same-ID sender resume, receiver restart, cancel/retry, verified completion and exactly-once raw/index/report ingest. Static source-string checks are insufficient.

PL-0134 remains unchecked.

Decision: **CHANGES_REQUIRED**
