# PL-0090 — ChatGPT Independent Audit V04

Decision: **CHANGES_REQUIRED**

## Independent finding

Discovery now uses ScanSessionStore.reopen and ContentView installs/discards real sessions. But the frozen integrated restart evidence is incomplete: SessionDiscoveryService tests do not cover each PL-0088 partial transaction stage, stale transactions, corrupt per-photo records/sources, version mismatch through discovery, and real discard behavior. Candidate-state-after-recovery is not comprehensively proven.

## Required remediation

Preserve all Batch-004 behavior that already passes. Close only the remaining production-seam or evidence gap above with behavior-bearing tests against the actual production-used seam. Do not add another disconnected helper.

PL-0090 remains unchecked.

Decision: **CHANGES_REQUIRED**
