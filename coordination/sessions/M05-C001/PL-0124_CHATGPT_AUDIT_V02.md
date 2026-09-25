# PL-0124 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

Receiver resumability remains sound, but the production iOS sender restart/resume requirement is not closed. SenderTransferIdentityStore is defined but unused. FinalizedTransferWorkflowView creates a request with transferID=nil. startNetworkTransfer generates a UUID but does not persist it into networkRequest. retryNetworkTransfer first queries the old in-memory transfer ID, then calls startNetworkTransfer(networkRequest); because that request still has transferID=nil, a new UUID can be generated, creating a second transfer instead of resuming the original. App restart recovery is therefore absent.

## Required remediation

Persist and restore the actual transfer ID/package digest/receiver identity when the first transfer starts, rebuild the request with that transfer ID after app restart, and make retry continue the same ID from receiver next_offset. Add fake production-client tests for sender restart, reconnect, cancel/resume and no-new-transfer behavior.

PL-0124 remains unchecked.

Decision: **CHANGES_REQUIRED**
