# PL-0093 — ChatGPT Independent Audit V04

Decision: **CHANGES_REQUIRED**

## Independent finding

Deletion now rejects non-authoritative plans, delete() throws on partial failure, and a real symlink escape test exists. The frozen criteria also require explicit missing-session and injected history-index failure coverage. Current Batch-004 tests cover session failure and symlink, but not the history-index partial-failure path or missing-session semantics through the public deletion API.

## Required remediation

Preserve all Batch-004 behavior that already passes. Close only the remaining production-seam or evidence gap above with behavior-bearing tests against the actual production-used seam. Do not add another disconnected helper.

PL-0093 remains unchecked.

Decision: **CHANGES_REQUIRED**
