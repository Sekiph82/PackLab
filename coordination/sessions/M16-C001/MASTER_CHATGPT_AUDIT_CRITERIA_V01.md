# M16-C001 - CI/CD, Signing & Distribution Master ChatGPT Audit Criteria V01

All criteria are mandatory for the pre-M17 M16 implementation batch.

1. Execution is authorized by live TASKS, starts synchronized, preserves owner-local work and runs PL-0347→PL-0367 in exact order.
2. Every completed child satisfies frozen criteria and has distinct implementation/evidence + log-only publication ending `READY_FOR_INDEPENDENT_AUDIT`.
3. Windows CI uses locked/reproducible Python quality checks with least-privilege permissions and secret-safe dependency caching.
4. Production Studio build packages the real app, binds version/build provenance and introduces no private data/runtime-download dependency.
5. Windows EXE/installer does not receive PASS unless actual shipped native/runtime inventory and required redistribution notices/licenses are reviewably closed.
6. Packaged Windows smoke exercises packaged bits and cannot mask startup failure.
7. CI/public artifact retention excludes private data, mutable project outputs and signing material.
8. Public CI does not depend on proprietary sample scans or pull M17 golden datasets forward.
9. macOS/iOS CI builds/tests unsigned by default, uses exact SPM resolution, and has no signing-secret requirement for PR/simulator/device-archive gates.
10. Optional signed IPA path is protected, secret-safe, ephemeral and skipped truthfully when credentials are absent.
11. Unsigned fallback/install documentation does not claim unsigned artifacts install directly on physical iPhone.
12. Repository guard prevents Apple signing material/secrets from entering the public repo.
13. iOS artifact provenance distinguishes simulator/unsigned archive/signed IPA and binds exact versions/digests/build tools.
14. iPhone 16 procedure is exact, credential-free and warns about data preservation before destructive reinstall.
15. Release numbering keeps Studio/Capture/PackScan domains independent while coordinating one release train.
16. Release manifest binds dependency/schema/artifact/signing/compliance facts and fails closed on missing required evidence.
17. Changelog uses accepted PL task IDs, not commit messages/builder logs as acceptance truth.
18. Release checklist requires independent Windows/iOS/security/compliance evidence and explicitly requires M17 before release.
19. Rollback preserves original .packscan/raw evidence and uses declared compatibility, never version guessing.
20. No tag/GitHub Release/V0.1 publication is created; PL-0368 remains exactly `DEFERRED_POST_M17`.
21. No M17+ implementation, Codex TASKS edit, private data, unreviewed dependency or secret leakage occurs.
22. Successful handoff records 21/21 executable children, `BATCH_COMPLETED_PRE_M17_GATE`, clean parity, M17-not-started, PL-0368 deferred and terminal `AWAITING_MILESTONE_AUDIT`; otherwise exact stopped frontier/blocker is recorded.

Independent audit must inspect actual source/workflows/build evidence and, where relevant, real GitHub Actions run evidence. Builder logs are evidence, never acceptance.
