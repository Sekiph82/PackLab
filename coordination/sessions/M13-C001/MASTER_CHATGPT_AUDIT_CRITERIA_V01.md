# M13-C001 - Master ChatGPT Audit Criteria V01

Milestone: **M13 - CAD/BREP & Engineering Export**
Scope: **PL-0289 through PL-0309**

All criteria are mandatory for a completed M13.

1. Tracker explicitly authorizes M13-C001 / READY / CODEX; M12 is AUDITED_PASS and M14+ is unauthorized.
2. PL-0289 selects an exact Windows CPython 3.12 compatible Python OpenCascade binding only after install/import/capability/license/artifact evidence; no runtime auto-download.
3. PL-0290 hides binding-owned API behind a PackLab CAD adapter and reports observed binding/kernel capabilities/versions truthfully.
4. PL-0291 converts valid revolve Design Models into derived BREP without mutating Design Model/Scan Master and preserves parent authority/unit state.
5. PL-0292 converts ordered loft Design Models with explicit failure diagnostics and no silent gap healing.
6. PL-0293 supports only authorized handle/simple-indent booleans from parametric feature geometry and never raw scan booleans.
7. PL-0294 reports topology/solid validity without silent repair and without equating valid BREP to physical/manufacturing validity.
8. PL-0295 named-feature mapping is lineage/evidence based and reports ambiguous/unresolved topological naming rather than silent retarget.
9. PL-0296 tessellation is bounded/deterministic PREVIEW_PROXY and preserves CAD/Design Model revision linkage.
10. PL-0297 STEP requires mm_unverified source for millimetre engineering export; RELATIVE is rejected; mm encoding does not upgrade physical authority.
11. PL-0298 printable STL requires explicit mm_unverified handling, bounded tessellation quality and mandatory unit/provenance sidecar; RELATIVE is rejected.
12. PL-0299 OBJ/GLB exports preserve stable part naming, exact source revisions and explicit unit/scale transforms without becoming CAD/Design Model truth.
13. PL-0300 canonical export manifest records project/revisions/authority/units/scaling/software/kernel/file digests/limitations deterministically and privacy-safely.
14. PL-0301 STEP round-trip checks software readability/topology/units/bounds using numerical tolerance, not physical tolerance.
15. PL-0302 UI clearly separates Scan Mesh and editable Design Model export and delegates all authority/unit gates to domain services.
16. PL-0303 orthographic views derive from canonical Design Model/CAD axes as vector-ready drawing geometry.
17. PL-0304 section views use explicit planes/heights and do not mutate or fabricate source geometry.
18. PL-0305 dimensions derive from source numerical geometry, not pixels; RELATIVE/mm_unverified labeling is correct.
19. PL-0306 title block records revisions/units/software and mandatory physical-authority disclaimer without private ambient identity.
20. PL-0307 SVG/DXF remain vector exports of shared drawing truth with correct unit metadata and provenance.
21. PL-0308 PDF uses a stable reviewed vector-preserving path or stops BLOCKED; it does not silently introduce a new dependency or replace SVG/DXF source truth.
22. PL-0309 validates drawing numerical values against exact Design Model/CAD values and distinguishes software tolerance from physical metrology.
23. Across M13, CAPTURED_SCAN_MASTER/STANDALONE_DESIGN_GEOMETRY authority remains explicit, Scan Master/Design Model are immutable with respect to derived CAD/export work, and no RELATIVE->mm or unverified->mold/manufacturing promotion occurs.
24. PL-0220 through PL-0224 remain deferred and are not satisfied by CAD/export success.
25. No M14+ implementation begins.
26. Every child has focused/negative/boundary/regression plus locked full-suite/static/scope/security/dependency evidence.
27. Every completed child has distinct implementation/evidence and log-only publication and ends `READY_FOR_INDEPENDENT_AUDIT`.
28. Master log truthfully records BATCH_COMPLETED or exact BATCH_STOPPED and ends `AWAITING_MILESTONE_AUDIT`.

Closure requires fresh independent ChatGPT child audits plus M13 milestone audit.
