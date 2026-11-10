# PL-0374 — Validation Criteria V01

1. The API compares the exact observed metric set against inclusive finite expected ranges and returns deterministic per-metric plus aggregate outcomes.
2. It fails closed on missing/extra/invalid metrics, invalid bounds and ambiguous dataset authority.
3. Provenance, units and synthetic-only measurement authority are preserved in result objects.
4. CI regression fixtures contain no licensed real dataset payloads or private scans.
5. A single comprehensive M17 test run and consolidated independent/security review are recorded before milestone tasks are accepted.
