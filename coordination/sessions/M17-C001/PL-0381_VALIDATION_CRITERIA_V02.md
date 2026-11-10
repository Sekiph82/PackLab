# PL-0381 — Validation Criteria V02

1. An injected zero-space provider deterministically rejects a project authority update before any authoritative or mirror bytes change.
2. A publish-time `ENOSPC` returns an actionable project error and leaves the prior authority/state/raw capture intact; task-owned temporary files are removed.
3. Free-space reader failure or malformed results fail closed without publishing.
4. No actual disk is filled and no unrelated/owner data is cleaned up.
5. A crash after durable authority publication remains recoverable by existing authority-to-mirror repair.
6. Tests execute only at the M17 milestone-end batch.
