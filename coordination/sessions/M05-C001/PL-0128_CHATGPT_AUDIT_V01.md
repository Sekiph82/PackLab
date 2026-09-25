# PL-0128 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The headless receiver is materially implemented and reuses the shared M05 services:
- configured host/port lifecycle;
- TLS-required server start;
- authenticated HTTP transfer routes;
- resumable transfer store;
- verified-only Capture Inbox publication;
- the same `ImportService` used by manual ingest;
- distinct transfer IDs.

However, the frozen PL-0128 evidence requirements are not fully satisfied.

### Required loopback integration tests are missing

The added receiver tests call `PackLabReceiver.create_transfer/put_chunk/complete` directly with `token_authenticated=True`. They do not start the HTTPS server and exercise the real network handler/authenticator.

They also do not test:
- clean receiver shutdown and restart with resumable checkpoint preservation;
- network status/resume after restart;
- paired HTTPS request versus missing/invalid Bearer credential over loopback.

The criterion explicitly requires loopback integration tests for paired transfer, unpaired rejection, shutdown/restart resume, verified inbox handoff, and concurrent transfer IDs.

### Pairing route dependency remains unresolved

The production HTTPS handler requires an already-issued Bearer token and has no network pairing endpoint, so a real iPhone cannot yet establish the authenticated receiver session through the receiver itself.

## Required remediation

Preserve the receiver service. Add the missing network pairing/auth route from PL-0123 and true TLS loopback integration tests that start/stop/restart the receiver, authenticate a client, resume a partial transfer, verify inbox handoff, reject unpaired requests, and keep concurrent transfers isolated.

PL-0128 remains unchecked.

Decision: **CHANGES_REQUIRED**
