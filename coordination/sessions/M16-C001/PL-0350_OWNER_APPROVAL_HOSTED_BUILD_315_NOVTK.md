# PL-0350 — Owner Approval for Checkpointed Hosted 315-Module No-VTK Build

Date: 2026-10-12
Ruling: **OWNER_AUTHORIZED_HOSTED_NATIVE_BUILD_315_NOVTK**
Source: owner explicitly responded `baslat` after independently audited static preflight and a direct request to authorize actual 315-module OCP compilation on GitHub-hosted Windows runners.
Task scope: **PL-0350 ONLY**. Approval permits preparing, implementing, testing and dispatching an explicitly gated, checkpointed, source-built **OCCT → official OCP 315-module generated C++ → PackLab unsigned installer** workflow on GitHub-hosted runners. It is **not** an approval for repeated six-hour monolithic attempts, a prebuilt opaque wheel substitution, private data upload, public release/signing, or new milestone work.

## Accepted architectural boundaries

1. Official OCP `7.9.3.1.1` release `OCP_src_stubs_Windows.zip` SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`, length 6,481,047 bytes. Upstream OCP source revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`. No pywrap rerun; no automatic fallback to generation. Verify 319 exact source triplets and 638 declarations/registrations BEFORE patch; remove ONLY `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK` using audited upstream No-VTK semantics, retain 315 complete generated module triplets and all CAD imports.
2. OCCT 7.9.3 is sourced/built from the exact repository-locked OCCT source/Windows toolchain, `USE_VTK=OFF`, no opaque `cadquery-ocp-novtk` wheel DLLs as shipped runtime. CPython 3.12.15 / Windows 2022 x64 / pinned MSVC, SDK, CMake, 4-worker contract remain immutable unless specifically audited/authorized.
3. Heavy compiles take place **on GitHub-hosted Windows runners**, NEVER on owner laptop. Before any implementation push that matches the old build workflow's `push` or `pull_request` filters, **first** ensure the legacy `windows-studio-build.yml` cannot auto-run its ~6h native job on those changes. Enable separate `workflow_dispatch` with an explicit affirmative input and fail-closed guards. Verify via GitHub Actions evidence; the disablement change itself must not accidentally launch the old producer. Other ordinary quality checks may run.
4. **Separate, durable, hash-verified stage checkpoints:** OCCT build/install SDK (~42m40s historically); official ZIP fetch/verification/deterministic 315 No-VTK patch and C++ extension compile (duration unknown); packaged CAD/QtPdf/Open3D + redistribution inventory/clearance + versioned unsigned installer. Distinct hosted jobs/stage outputs; do not assume any job can exceed GitHub's six-hour hosted limit. Exact input-based cache keys and content manifests; tampered/stale results fail closed.
5. Run tiny static fixtures and short focused/regression checks before a heavy dispatch. Dispatch **one** controlled cold workflow attempt, not concurrent/repeated uncontrolled copies. On failure stop and report exact blocked stage and persist successful earlier checkpoints. A subsequent verified warm cache-hit run is authorized **only after** the first cold workflow passes, to prove no repeated expensive native stages.
6. Require full capability and source/license/notice clearance. The historical opaque wheel's **79 unverified native-source rows** are not silently cleared by this authorization. Engineering package clearance must report zero unresolved shipped files/components, zero missing notices/sources, zero forbidden Qt modules, real frozen no-network CAD/STEP/DXF/PDF/Open3D smoke. Preserve `legal_review_required=true`, `public_release_authorized=false`. Do not claim legal signoff or sign/release installers.
7. Preserve current and previous-good owner `PackLab.exe` and OwnerDev while experimental hosted build is incomplete; no desktop compilation, large temporary trees, unrelated uv cache pruning, AppData deletion, forced merges, private uploads or secret exposure. Any later safe OwnerDev refresh follows existing project policy non-destructively with previous-good fallback. Root `TASKS.md` and independent ChatGPT audit verdict files remain ChatGPT-only.
8. PL-0350 is *complete only upon independent audit* after a genuine unsigned installer with package/compliance evidence. No PL-0351 clean-Windows test until that installer exists and the PL-0350 independent audit authorizes continuation; no M17 and PL-0368 remains deferred.

## Execution authority

Codex is **authorized NOW** to implement the owner-approved hosted native build plan and launch the explicitly gated GitHub-hosted cold workflow if the safety/feature/provenance preflight passes. No further owner response is needed to start *this single controlled attempt*. Hard blocker, unavailable capability, mismatch, missing source proof or unexpectedly costly change triggers an honest `BATCH_STOPPED_AT_PL-0350` handoff, not a retry or a new assumption.

Implementation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_PROMPT.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CHATGPT_AUDIT_CRITERIA.md
