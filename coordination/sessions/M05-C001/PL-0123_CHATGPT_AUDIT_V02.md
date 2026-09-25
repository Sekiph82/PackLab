# PL-0123 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

The HTTPS /v1/pair route, scoped bearer credentials and production pinned URLSession client are now present. However the mandatory network-boundary evidence remains incomplete. The loopback tests use ssl._create_unverified_context(), so they do not exercise certificate pinning/wrong-pin rejection; they also do not cover expired/replayed pairing through /v1/pair. OpenSSL-gated TLS tests were skipped on the builder. In-memory PairingAuthenticator tests do not substitute for the frozen real network-boundary wrong-pin/expiry/replay cases.

## Required remediation

Add deterministic network tests that can run without an external openssl executable, or generate/use ephemeral test TLS material through a declared test dependency/fixture. Exercise successful TLS pairing, actual certificate pin mismatch, expired/replayed offer, missing auth and wrong receiver over the real HTTPS endpoint.

PL-0123 remains unchecked.

Decision: **CHANGES_REQUIRED**
