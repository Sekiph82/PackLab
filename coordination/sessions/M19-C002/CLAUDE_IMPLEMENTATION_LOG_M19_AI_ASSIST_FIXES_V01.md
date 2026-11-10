# Claude implementation log — M19 AI-assist review fixes (V01)

Date: 2026-11-10. Implementer: Claude Code. This is not a review. It responds to
`CLAUDE_PEER_REVIEW_M19_AI_ASSIST_V01.md`.

| Finding | Change |
| --- | --- |
| F-1 P1 (PL-0423) | `accept_dimension_fit_proposal` now requires the user's own `request=`. Any proposal whose echoed request differs (targets, tolerances, deviation budget, deviation evidence) is rejected with `proposal_request_mismatch`. Tests cover widened tolerance, a moved target, a swapped budget and swapped evidence. |
| F-2 P2 (PL-0424) | New finding `mesh_topology_evidence_incomplete` for missing or malformed component, boundary or nonmanifold counts (point-cloud statistics, bool, float, negative). Counts are validated by `_count`. |
| F-3 P2 (PL-0421..0423) | Provenance IDs must match `[A-Za-z0-9][A-Za-z0-9._+:@-]{0,159}`, so no paths, spaces or control characters. `tests/core/test_m19_provenance_ids.py` adds 111 cases. |
| F-4 P2 (PL-0421) | Moving from OTHER to a suggested family clears `other_family_label`. Tested, together with rejection of a label on a non-OTHER choice. |
| F-5 P2 (all) | Feature flag `AppConfig.ai_assist_enabled` (default **False**; TOML key or `PACKLAB_AI_ASSIST_ENABLED=true|false`, strictly boolean). The fallback is the existing manual workflow, because the proposal APIs never mutate anything. No Studio UI calls these APIs yet; wiring the flag into a UI is future work. |
| F-6 P2 (PL-0423) | `BoundedGridFitOptimizer`: a deterministic stdlib reference optimizer. It runs a 5-step grid inside each measured tolerance (at most 625 evaluations) with a caller-supplied deviation evaluator and keeps only candidates within the deviation budget. A test shows it finds a known synthetic optimum and that its result can be accepted. |
| F-7 P2 (tests) | New tests cover: PL-0421 label rejection; PL-0422 unordered or repeated transitions; PL-0423 candidate/constraint set mismatch; PL-0424 nonmanifold and hole-report rules and `not_evaluated` confidence. |

Not addressed (P3): raw exception types on some malformed inputs; the accept functions take the suggestion object rather than the digest the user was shown; the confidence report is not tied to the geometry.

Local evidence: `pytest tests/core tests/studio` all pass; ruff and mypy are clean. Every external gate stays pending: any real model or checkpoint, physical validation of fits, and validation against real scans.
