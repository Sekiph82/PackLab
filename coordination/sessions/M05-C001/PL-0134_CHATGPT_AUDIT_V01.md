# PL-0134 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The final integration test module is valuable and exercises much of the Windows service chain:
- partial transfer state followed by receiver-object restart/resume;
- successful checksum verification;
- Capture Inbox publication;
- validation;
- immutable raw storage;
- dedupe;
- import report generation;
- cancellation/resume;
- whole-transfer digest mismatch;
- corrupt/bad/future/unsafe package quarantine.

The frozen PL-0134 criteria are not fully satisfied.

### It does not span the actual iOS transfer client/protocol artifacts

The tests construct Python `TransferCreate` objects and call `PackLabReceiver` methods directly with `token_authenticated=True`. They do not consume Swift/iOS protocol fixtures, a production iOS sender, pairing, TLS pinning, or the real HTTP network boundary. Because PL-0121–PL-0126 are not yet production-complete, this cannot serve as the required end-to-end iOS-transfer → Windows-ingest evidence.

### Missing-photo fixture does not isolate the required failure

`_missing_photo()` builds a ZIP with manifest + metadata but omits `checksums.json` as well as the image. `validate_packscan` therefore fails first on a missing required control entry; the test does not prove the missing image/photo payload path requested by the frozen criterion.

### Receiver restart is object-level, not lifecycle/TLS-loopback

The test recreates `PackLabReceiver` over the same storage root but never starts/stops the HTTPS service, so it does not prove the actual receiver lifecycle and network resume path.

## Required remediation

After the iOS sender/pairing/TLS work is production-composed, extend the integration suite to drive the real protocol boundary or authoritative cross-language client seam. Add a valid-control ZIP missing only the declared image/photo payload, and add receiver start/stop/restart resume coverage with authenticated transport while retaining deterministic local-only tests.

PL-0134 remains unchecked.

Decision: **CHANGES_REQUIRED**
