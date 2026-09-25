# PL-0121 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

## Independent finding

The batch establishes a useful PackLab Transfer Protocol V1 foundation:
- shared protocol name/version/HTTPS requirement;
- opaque finalized `.packscan` transfer identity;
- receiver/transfer/capture/package IDs;
- package size and SHA-256;
- chunk offset/length/digest;
- Python status and completion acknowledgement models;
- stable Python error codes;
- a Python golden create-message fixture with future-version and insecure-transport rejection.

However, the frozen PL-0121 criteria are not fully met.

### Cross-language contract is incomplete

The Swift side currently defines only:
- `TransferCreateMessage`;
- `TransferChunkMessage`.

It does not define/validate the corresponding status/query, completion acknowledgement, cancellation, or stable error envelope models required by the frozen protocol scope.

### Required cross-language tests are missing

The golden fixture is exercised only by Python tests. The final Swift test target contains no PL-0121 golden fixture/encoding/decoding test proving Swift field names match the Python contract, and no Swift-side version/error mapping validation.

### Idempotent retry/resume is not part of the V1 wire contract itself

Receiver-side idempotency is implemented later in PL-0124, but PL-0121's frozen protocol definition does not fully specify/query cancellation/resume messages or response/error envelopes in the shared Swift/Python contract.

## Required remediation

Preserve the existing protocol constants and create/chunk structures. Complete the shared V1 wire model on both Swift and Python for status/query, cancellation/resume, completion acknowledgement and stable error responses. Add one authoritative golden fixture set that both Swift and Python tests consume, including version rejection and error-code mapping.

PL-0121 remains unchecked.

Decision: **CHANGES_REQUIRED**
