# M07-C001 — Master ChatGPT Audit Criteria V01

Milestone: **M07 — Reconstruction Backends & Photogrammetry**  
Scope: **PL-0158 through PL-0165**

All criteria are mandatory.

1. Root TASKS.md authorizes M07-C001 / READY / CODEX before material work.
2. Read and preserve:
   - https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md
   - https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md
   - https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md
   - https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/RISK_REGISTER.md
3. PL-0135 through PL-0157 remain accepted and unregressed.
4. PL-0068 remains OWNER_REQUIRED.
5. Codex does not edit TASKS.md or ChatGPT audit/criteria artifacts.
6. Execute exactly PL-0158 through PL-0165 in task-ID order.
7. Every child reads its own frozen prompt/criteria before implementation and publishes a distinct child CODEX_LOG.
8. No PL-0166+ reconstruction pipeline work is started.
9. No OpenReality runtime dependency, VGGT checkpoint, SAM 3D Objects model or TRELLIS model is installed by this batch.
10. OpenReality-derived architecture is implemented as PackLab-owned interfaces/authority, not by copying room/navigation/MCP product features.
11. PL-0158 records an exact tested COLMAP version/source/license/build identity and makes no unsupported redistribution claim.
12. PL-0159 records an exact tested OpenMVS version/source/build identity and explicit AGPL high-attention status.
13. PL-0160 and PL-0161 probes are deterministic, non-destructive and distinguish absent, invalid, unsupported and valid engine states.
14. PL-0162 uses explicit configuration and safe discovery; it does not silently download/install engines.
15. PL-0163 satisfies https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md including ScaleState authority and a backend-neutral normalized manifest.
16. PL-0163 contains a future neural-backend seam only. No neural model is selected, downloaded or treated as measurement authority.
17. PL-0164 records bounded stdout/stderr, timing, exit/cancel/failure state and machine-readable stage evidence without leaking secrets/private portable paths.
18. PL-0165 preserves immutable RAW_CAPTURE, creates isolated retry-safe reconstruction workspaces/revisions and cannot corrupt a previously valid result.
19. Existing ProjectManager, JobManager, subprocess-runner, recovery, provenance and invalidation authorities are reused rather than shadowed.
20. Focused tests pass for every child.
21. Exact full locked suite exits 0.
22. Ruff, targeted/relevant mypy, compileall, project/static checks and git diff --check pass truthfully.
23. Known unrelated repository-wide mypy debt may be reported but no changed module may add an error.
24. Dependency/lock/license, protected-file, privacy/secrets, signing-material and generated/binary reviews pass.
25. Each child uses separate implementation/evidence and log-only commit boundaries.
26. Every child log uses full GitHub URLs and ends exactly READY_FOR_INDEPENDENT_AUDIT.
27. Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_LOG_V01.md indexing all eight child tasks, exact commits/checks/limitations, and ending exactly AWAITING_MILESTONE_AUDIT.
28. Do not start M07-S02 until independent ChatGPT audit accepts this batch.

Closure requires independent ChatGPT audit. Codex must not self-audit.
