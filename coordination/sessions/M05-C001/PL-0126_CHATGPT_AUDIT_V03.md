# PL-0126 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent result

The real history → FinalizedTransferWorkflowView → TransferScreen path is preserved, and it now benefits from PL-0124 same-ID retry/restore. Cancel calls the production client and retains sender identity/source.

However, the V03-required fake-client UI/service matrix is still incomplete. The only combined new PL-0124/0126 fake-client test proves same-ID persistence, cancel, status query, retry and runtime restore. The older PL-0126 tests prove confirmed-byte progress and basic authenticated completion, but there is no fake production-client behavior test for checksum retryable failure or terminal network failure, and no explicit runtime-restore assertion that the visible UI phase/progress is rebuilt from persisted sender identity plus receiver status.

Additionally, the current FakeProductionTransferClient supports only acknowledgementState = receiving/complete; it cannot exercise a terminal failure or digest-corruption response.

## Required remediation

Extend the injected ProductionTransferClient fake and tests to cover network cancel call, authoritative same-ID resume, monotonic receiver-confirmed progress, checksum/digest retryable failure, terminal network failure, verified completion, and a fresh TransferViewModel restore whose UI phase/confirmed bytes are derived from persisted identity + receiver status.

PL-0126 remains unchecked.

Decision: **CHANGES_REQUIRED**
