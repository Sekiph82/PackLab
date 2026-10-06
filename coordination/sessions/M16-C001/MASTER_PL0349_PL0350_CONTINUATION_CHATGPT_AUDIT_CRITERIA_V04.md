# M16-C001-R03 - PL-0349/PL-0350 Continuation Master Audit Criteria V04

All criteria are mandatory.

1. PL-0347 V02 and PL-0348 remain independently accepted and unchanged except genuinely required packaging seams.
2. PL-0349 V02 proves the frozen production application includes and executes required Qt, OCP/CAD and Open3D runtime capabilities without network/download.
3. PL-0350 V03 runs only against that capability-complete stage.
4. No required feature/dependency is omitted merely to simplify redistribution.
5. Qt shipped surface is minimal and justified; GPL-only/unaccepted Qt modules are absent under the current route.
6. External Windows runtime prerequisites are not falsely reported as shipped PackLab binaries and post-prune frozen capability smoke remains green.
7. CPython/OpenSSL, PyInstaller hooks, OCP/OCCT and Open3D are mapped truthfully at actual shipped-file level.
8. Required license/notice/source evidence is exact/version-pinned and missing evidence fails closed.
9. PL-0350 green state remains engineering packaging clearance only, with legal review/public-release gates explicit.
10. PL-0351 through PL-0367 begin only after both remediation children are builder-green and execute in exact order.
11. PL-0368 remains `DEFERRED_POST_M17`; no Git tag/GitHub Release or M17 implementation occurs.
12. Every completed child has distinct implementation/evidence and child-log publication ending `READY_FOR_INDEPENDENT_AUDIT`.
13. Real blockers stop truthfully; successful completion records `BATCH_COMPLETED_PRE_M17_GATE`, clean parity, M17-not-started, PL-0368 deferred and terminal `AWAITING_MILESTONE_AUDIT`.

Independent audit must inspect source/diffs, hosted build/runtime capability evidence and exact compliance/source artifacts. Builder logs are evidence, never acceptance.
