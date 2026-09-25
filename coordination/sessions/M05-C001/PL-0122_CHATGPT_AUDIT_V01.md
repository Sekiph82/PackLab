# PL-0122 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The implementation provides a useful pairing domain model on both sides:
- Windows creates short-lived one-time offers containing receiver ID, host/port, pairing ID/code, expiry and TLS fingerprint.
- Python exposes a QR payload containing the same offer.
- iOS can decode a `PairingOffer`, normalize manual codes, and has an explicit `PairingCameraOwnership` actor that prevents capture and pairing-scanner ownership from overlapping.
- Python tests cover expiry, wrong receiver, wrong pin, replay, malformed QR and wrong version.

The frozen task still requires production workflow features that are absent.

### iOS manual/QR pairing is not exposed in the application

There is no pairing screen, manual code entry flow, QR scanner UI/composition, or production call path in `ContentView.swift`. `PairingCameraOwnership` is therefore not connected to the actual production camera owner.

### No persistent minimum reconnect identity on iOS

A Python `PairedReceiverIdentity` exists in the receiver-side pairing store, but the iOS app has no persisted receiver identity store for reconnect and no proof that the one-time pairing code is excluded from such persistence.

### Required Swift behavior tests are missing

The final Swift test target contains no PL-0122 tests for:
- QR payload parsing;
- manual code normalization/entry;
- expired/wrong-version/malformed offer handling on iOS;
- non-concurrent production camera ownership and clean hand-back.

## Required remediation

Preserve the current pairing contracts. Add a real iOS pairing coordinator/UI with manual-code and QR flows, wire scanner ownership to the production capture camera lifecycle, persist only receiver ID/host/port/fingerprint for reconnect, and add deterministic Swift tests for all frozen failure and ownership cases.

PL-0122 remains unchecked.

Decision: **CHANGES_REQUIRED**
