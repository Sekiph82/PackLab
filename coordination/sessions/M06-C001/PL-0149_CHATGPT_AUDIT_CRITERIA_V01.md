# PL-0149 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. Existing project/raw authority and single viewport abstraction are preserved.
5. PL-0149 satisfies the frozen scope.
6. Define dependency/provenance metadata linking derived artifacts to upstream project revision/input digests/settings.
7. When an upstream authoritative input or relevant parameter changes, mark affected derived artifacts stale/invalid without deleting raw or unrelated derived outputs.
8. Provide deterministic invalidation propagation and a query API for UI badges/job planning.
9. Persist provenance atomically and detect missing/tampered upstream inputs.
10. Add tests for direct and transitive invalidation, unrelated change, parameter change, stale reopen and raw non-mutation.
11. Tests/benchmarks exercise the production-used service/viewport seam rather than only mocked policy helpers.
12. Performance/native/GPU claims are measured and limitations are stated truthfully.
13. Full locked suite and relevant Ruff/mypy/compileall/project checks pass.
14. Dependency/lock/license changes are reproducible and compliant.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
