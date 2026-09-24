# PL-0118 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Shared M03/M04 capture, quality, coverage and session architecture is reused.
5. PL-0118 satisfies the frozen scope.
6. Implement one deterministic preflight that evaluates selected preset, device/session readiness, storage/thermal/battery admission, calibration availability, preparation acknowledgements and minimum environment guidance before capture starts.
7. Differentiate hard blockers, warnings and informational guidance with stable reason codes.
8. PL-0068 calibration remains OWNER_REQUIRED; absence of owner-verified physical calibration must be represented truthfully and must follow the approved policy rather than fabricated acceptance.
9. Preflight must feed the real New Scan/start-capture workflow and persist its result/acknowledgements with the session.
10. Add table-driven tests for all presets, blockers/warnings, unavailable calibration, health conditions and exact start-eligibility behavior.
11. Preset/mode behavior is config-driven and persisted with session context.
12. No unsupported physical/reconstruction capability is claimed.
13. Tests exercise the production-used preflight/preset/session seam.
14. Relevant regression/project checks and git diff --check pass truthfully.
15. Privacy/signing/secret boundaries remain clean.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
