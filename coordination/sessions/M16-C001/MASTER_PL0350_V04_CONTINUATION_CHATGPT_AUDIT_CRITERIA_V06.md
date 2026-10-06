# M16-C001-R05 - PL-0350 V04 Continuation Master Audit Criteria V06

All criteria mandatory.

1. PL-0347 V02 through PL-0349 V03 remain independently accepted.
2. OWNER DEV launcher remains AUDITED_PASS and post-Codex refresh runs after each new published child.
3. PL-0350 V04 closes the exact current shipped-file/component/source/notice engineering surface; no stale artifact substitution.
4. No required Qt/PDF/OCP/Open3D feature is removed merely to simplify redistribution.
5. PL-0350 green state requires zero unresolved shipped files/components/missing notices/source packages plus a versioned unsigned installer.
6. PL-0351 starts only after PL-0350 V04 is builder-green.
7. PL-0351 tests the downloaded/installed exact installer artifact in a separate sanitized Windows job and hard-fails native loader/procedure/entry-point errors.
8. PL-0352 through PL-0367 begin only after PL-0351 is builder-green and execute in exact order.
9. Every completed child publishes distinct implementation/evidence and child log ending `READY_FOR_INDEPENDENT_AUDIT`.
10. No private data/secrets/signing material leakage, tag/GitHub Release/V0.1 publication, M17 implementation or PL-0368 execution.
11. PL-0368 remains `DEFERRED_POST_M17`.
12. Successful batch ends `BATCH_COMPLETED_PRE_M17_GATE` + `AWAITING_MILESTONE_AUDIT`; any real blocker stops truthfully.

Independent audit must inspect source/diffs, hosted compliance/source artifacts, installer provenance and separate clean-install evidence. Builder logs are evidence, never acceptance.
