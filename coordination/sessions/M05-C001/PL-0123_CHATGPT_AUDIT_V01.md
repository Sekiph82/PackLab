# PL-0123 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The implementation has sound security building blocks:
- Windows receiver refuses to start without a TLS identity and wraps its HTTP server socket in a TLS server context.
- Pairing authentication issues random scoped bearer credentials, stores only token hashes server-side, enforces expiry/receiver/fingerprint/HTTPS checks, and supports revocation.
- iOS includes a certificate-fingerprint-pinning URLSession delegate.
- No private key or bearer token is committed.

The frozen PL-0123 criteria still require an end-to-end production security seam that is not implemented/proven.

### Pairing/authentication is not available over the production network workflow

`PackLabReceiver.pair(...)` is only a direct in-process Python method. The HTTPS receiver exposes transfer routes that already require a Bearer token, but it exposes no network pairing endpoint through which the iPhone can exchange the short-lived pairing offer/code for that token.

### iOS TLS/auth is not composed into a transfer client

`PinnedReceiverSessionDelegate` exists, but no production iOS URLSession transfer client constructs a pinned session, performs the pairing exchange, stores the scoped credential, or sends authenticated create/status/chunk/complete requests.

### Frozen certificate/TLS integration tests are missing

`tests/transfer/test_security.py` exercises `PairingAuthenticator` as an in-memory policy model. It does not generate an ephemeral certificate, start the HTTPS receiver, perform a successful TLS/authenticated request, and prove wrong-pin/missing-auth behavior over the actual socket. There is likewise no Swift test of the pinning client seam.

## Required remediation

Preserve the existing TLS identity, authenticator and pinning delegate. Add a production network pairing/auth endpoint and a real iOS pinned/authenticated transfer client that consumes the pairing offer. Add loopback TLS tests using an ephemeral certificate for successful pairing/authenticated transfer request, wrong pin, expired/replayed code, missing auth, wrong receiver and redacted secret behavior.

PL-0123 remains unchecked.

Decision: **CHANGES_REQUIRED**
