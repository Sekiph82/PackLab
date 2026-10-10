# PL-0350 V07-R01 — Independent Audit Criteria for Checkpointed Native Build

Parent audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V07.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_V07_R01_PHASE_SPLIT_CODEX_PROMPT.md

**Acceptance is an actually working unsigned installer, not source strings, timeout increases or simulations.**

## Mandatory R0 recovery/owner-go gate (supersedes automatic cold-run authorizations)

- Inspect actual GitHub artifacts/cache and bounded known-runtime inventory, **without fresh native compile**, to establish whether completed OCCT and pywrap results are durably reusable. Three inspected prior runs (`37967978530`, `37951025064`, `37860820132`) expose zero run artifacts; repository logs by themselves are not reusable binaries. Check caches and any other eligible sources separately, never silently assume success or absence without inspection.
- Read-only `PL-0350_R0_RECOVERY_INVENTORY.md` distinguishes exact-verified checkpoint, incomplete/opaque candidate, and only log/progress evidence; hashes/source locks/required files/size/timing/ownership for any candidate.
- **NO rerun of OCCT or pywrap on a newly provisioned runner unless the owner expressly authorizes the exact necessary phases after recovery inventory.** No monolithic six-hour retry, no no-op cache simulation, no unapproved changes to official build provenance, no 65 GB local test build.
- If a cryptographically verified reusable checkpoint allows later processing, continue only from the next required stage, preserving safety/packaging checks. If no appropriate checkpoint survives, stop and request decision (`OWNER_APPROVAL_REQUIRED_FOR_NATIVE_REBUILD`), not `AUDITED_PASS`.
- This R0 HOLD overrides anything in the remaining numbered checklist which presumes a previously authorized cold run. The implementation may be prepared/tested using tiny mocks while held; real long builds must wait.



1. Canonical origin/main TASKS authorizes this remediation. Dirty owner work, all active/unpublished worktrees, current and previous OwnerDev untouched. ChatGPT-only files not modified by Codex.
2. Actual V07 canceled evidence used to define stage boundaries; preflight timed/size plan for all four hosted jobs exists before cold run. No job assumes >360 minutes, no unsupported worker-count increase.
3. Job A really builds exact SHA-locked OCCT and produces a *portable minimal SDK checkpoint* with sealed artifact manifest, exact file hashes and pinned source/toolchain. No source/build-tree private debris in shipped runtime.
4. Job B consumes the exact verified OCCT checkpoint *without OCCT rebuilding*, runs all 319 pywrap modules at locked four workers, records actual time including setup/hash/upload, uploads validated generated sources. If >6h predicted, no expensive run until fixed.
5. Job C uses a **fresh job runner**, imports hash-validated generated source/OCCT checkpoints, recompiles with newly configured CMake paths, never runs OCCT or pywrap stages, builds actual OCP.pyd, seals and smokes it. Prove portable relocation/reconfiguration.
6. Job D consumes validated final runtime of the *same workflow run*, not directly a cross-run cache, removes opaque wheel OCP libraries, runs actual Qt/PDF/OCP/CAD/Open3D packed smoke and full redistribution audit.
7. Every cache key uses exact relevant source-lock, builder/validation, toolchain and schema inputs; no broad restore keys; reject injected stale/modified/extra files. Cache HIT validation and second real hosted cache-hit run show **no** OCCT/pywrap rebuild.
8. Each stage has its own actual run duration / exit status, checkpoint artifact names, file count/bytes/hashes and upload/download proof. Artifact storage limits, expiration and retention accounted for before multi-hour run; no private data or secrets published.
9. Cold job evidence really produces a final sealed OCP runtime and bundle; warm job proof really reuses exact bytes. No substitution of a mocked/test-only smoke for final acceptance.
10. Redistribution/source/license/notice/forbidden Qt unresolved counts all zero and engineering package cleared. Unsigned installer built, versioned, uploaded only thereafter. No public release/legal-pass assertion.
11. Fresh end-to-end Windows quality, relevant focused and full regression, static checks, source lock/manifest integrity and local disk safe-wrapper checks PASS. Any pre-existing quality exception is explicit.
12. Owner Desktop native EXE refreshed and usable; no standalone portability proof inferred from OwnerDev. No developer environment or private project data in artifact.
13. Stop truthfully at first hard blocker; partial artifacts kept for safe resume, **never** re-run same six-hour cold phase blindly. PL-0351 only starts after cleared installer; PL-0352... in exact order after clean-install smoke PASS. PL-0368 remains deferred and M17 not started.
14. Independent audits and root TASKS remain ChatGPT-only. Logs and implementation separate commits, GitHub links and final origin/main readback verified.

**Verdicts**:
- `AUDITED_PASS` only if every PL-0350 installer/security/hosted-cache gate is evidenced.
- Otherwise `AUDITED_CHANGES_REQUIRED` with precisely named blocked phase. Do not increment arbitrary V-number to count blocked iterations.
