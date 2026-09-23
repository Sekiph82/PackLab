# PL-0090 — ChatGPT Remediation Audit V03

Decision: **CHANGES_REQUIRED**

## Independent finding

Launch discovery now consults ScanSessionStore.reopen, ContentView installs a real ActiveScanSession on Resume, and Discard invokes safe deletion. The frozen restart evidence remains incomplete: tests do not exercise discovery/resume through partial transaction recovery, stale transaction stages, missing/corrupt per-photo records, version mismatch, and real discard. The integrated restart/recovery seam is therefore not yet proven.

The Batch-003 implementation is retained as valid progress. Builder log format, protected files, and Windows regression claims are otherwise consistent.

## Required remediation

Repair the exact remaining transactional/authoritative boundary above and add behavior-bearing filesystem tests for the failure mode. Preserve all already-correct Batch-003 behavior.

PL-0090 remains unchecked.

Decision: **CHANGES_REQUIRED**
