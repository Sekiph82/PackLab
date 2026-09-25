# PL-0125 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

The production Swift code is hardened correctly: URLSessionTransferClient and TransferViewModel now require matching transfer ID, matching package digest, authenticated=true, verified=true, and terminal verified/complete state before completion; resumable identity is retained on rejection.

The frozen V03 test matrix is not completed. The only new PL-0125 Swift test checks wrong transfer ID and non-terminal state. Existing PL-0126 coverage checks unauthenticated acknowledgement, but the final Swift test suite contains no explicit production-client tests for:
- wrong package digest;
- final-byte/package corruption or wrong declared digest;
- retry after digest mismatch;
- the URLSessionTransferClient acknowledgement gate itself.

The V03 criterion explicitly required an injected ProductionTransferClient/URLProtocol matrix for these cases.

## Required remediation

Add production-client-level tests for matching success, wrong transfer ID, wrong digest, unauthenticated acknowledgement, non-terminal acknowledgement, corrupted/wrong-declared package digest, retry after mismatch and no premature completion/identity clearing. Exercise URLSessionTransferClient validation through an injected URLProtocol/transport seam, not only TransferViewModel.applyCompletion.

PL-0125 remains unchecked.

Decision: **CHANGES_REQUIRED**
