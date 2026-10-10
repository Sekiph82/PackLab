# PL-0350 V07-R01 — CHECKPOINTED OCCT / PYWRAP / OCP Windows Packaging Recovery

Repo: https://github.com/Sekiph82/PackLab
Branch: `main`
Executor: CODEX
Purpose: **get the real standalone unsigned Windows PackLab installer**, not another six-hour canceled monolithic run.
This is one focused remediation **inside PL-0350**, not a new product milestone.

Independent authoritative audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V07.md
Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_V07_R01_PHASE_SPLIT_CHATGPT_AUDIT_CRITERIA.md
Parent frozen V07 source/provenance/compliance authority:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V07.md
Required Codex log:
`coordination/sessions/M16-C001/PL-0350_V07_R01_PHASE_SPLIT_CODEX_LOG.md`
Master handoff log:
`coordination/sessions/M16-C001/MASTER_PL0350_V07_R01_PHASE_SPLIT_CODEX_LOG.md`

## OVERRIDING OWNER HOLD — RECOVER FIRST; NO AUTOMATIC NATIVE REBUILDS (2026-10-10)

The owner questioned why OCCT and full pywrap must run **again** when both already completed on the prior GitHub runner. This hold supersedes any implied authorization elsewhere in this prompt or its parent to launch a cold native build. Do NOT begin OCCT compilation, pywrap generation, generated C++ compilation, a long hosted Actions cold-cache run, or any large local build until the owner explicitly approves the exact unrecoverable phases and new cost/time plan. Read-only inventory, audit of proofs, short static/unit checks, and safe design changes are allowed.

**Recovery Gate R0: read-only, zero expensive rebuilds**

1. Check prior workflow run artifacts and verified per-stage/producer caches for `37967978530`, `37951025064` and `37860820132`; latest API inspection returned ZERO workflow artifacts for all three. Separately query GitHub Actions caches by exact key and verify hashes/schema; do not confuse successful step logs or generic package uv cache with durable OCP or generated-C++ artifacts.
2. Inspect other prior successful Actions artifacts, current/previous known-good OwnerDev release manifests, existing official prebuilt OCP wheels and package caches **read-only and with bounded enumeration only**. If a candidate truly contains exact corresponding OCCT installed SDK, generated OCP C++ source, or compiled `OCP*.pyd`, verify source-lock, compiler/CPython compatibility, complete SHA manifest/attestation, redistribution evidence, and usability; do not copy questionable binaries or infer that a runtime wheel's executable bytes prove their corresponding build-source provenance. Protect active runtime and private data. Never scan 60+ GB of ambiguous legacy AppData or alter shared caches to look for salvage.
3. Distinguish: (a) verified reusable exact-current checkpoint (skip ONLY matching completed phase and continue from next safe phase), (b) historical output with incomplete provenance (potential alternative requiring independent review/owner approval), (c) mere log/progress, not recoverable binary, (d) no surviving output. Do not infer a saved bundle from a completed OCCT/pywrap stage.
4. Publish `PL-0350_R0_RECOVERY_INVENTORY.md` with exact GitHub links, cache keys, artifact names/hashes/sizes, allowed vs unsafe candidates, work already performed, feasibility/time bounds, and minimum required rebuild if any.
5. If existing, verifiably complete checkpoint(s) make actual remaining compilation/packaging feasible WITHOUT rerunning OCCT or pywrap, proceed only through the preserved downstream stages subject to the usual product/safety gates. **If even one OCCT/pywrap native phase needs re-execution, STOP and hand over `OWNER_APPROVAL_REQUIRED_FOR_NATIVE_REBUILD` with one precise plan; do not start it.** Explicit owner approval to re-run the named phase(s) is a prerequisite that this file cannot grant retroactively.
6. The test suite or a successful importer cannot substitute for missing native runtime binaries. Do not fake output, reduce the CAD feature set, or replace a locked source-built runtime with opaque wheels without fresh independent provenance review and owner consent.

**The phase-split job architecture below remains the implementation design for a future explicitly approved cold run; it is NOT authorization to execute one now.** In particular, the later original phrase "one authorized initial cold run" is revoked by this hold. Preserve the Desktop EXE and previous-good artifacts. Do not launch a six-hour retry.

## Before modifying: canonical and timing decisions

- Fetch origin, read `git show origin/main:TASKS.md`; explicitly require live authorization for this R01. Preserve dirty owner Desktop checkout and unpublished or active worktrees; use clean managed worktree. Do NOT modify root TASKS.md or ChatGPT audit documents.
- Examine actual canceled job https://github.com/Sekiph82/PackLab/actions/runs/37967978530 and V07 source. It spent 2,560.860 seconds OCCT, 18,220.375 seconds pywrap and started OCP generated C++ compile 8.5 minutes before cancellation. GitHub-hosted **per-job** execution limit is six hours (even if YAML says 480).
- Record exact native source lock/toolchain/build-contract hashes. Preserve 4 workers and current source-built OCP/OCCT, exact revision provenance, extension/full-feature and redistribution gates. Do not turn source build into opaque prebuilt wheel.
- Before any long hosted run, publish a **measured phase plan**: inputs/artifact paths, files/exclusions, exact stage cache key, rough artifact bytes, expected per-stage wall time, time left for setup/upload, maximum GitHub artifact/cache constraints. If the 5h04m pywrap stage will not fit once setup and handoff are accounted for, do NOT rerun and do NOT declare plan green; first optimize/partition pywrap safely while keeping full 319-module output and identical source inputs.

## Build architecture: distinct hosted jobs with durable source-verified checkpoints

**Job A: OCCT build/verified SDK producer**
- Fetch SHA-locked original OCCT sources; build/install locked OCCT 7.9.3 once.
- Export *minimal sufficient* OCCT headers/libs/cmake/runtime DLLs and exact validated source/provenance metadata (not whole compiler or source/build trees).
- Hash each file + deterministic canonical manifest; fail closed on file mismatch, unexpected files, wrong toolchain or source lock. Cache/upload source-identified checkpoint for downstream jobs.

**Job B: pywrap C++ generation**
- Consume verified same-run or exact-input restored OCCT SDK checkpoint, never rebuild OCCT.
- Regenerate full OCP/pywrap 319 modules with **N_PROC=4**, pinned locked source and toolchain.
- Export only generated C++/headers/CMake plus minimal necessary pinned inputs. Do **not** export platform-private paths or stale CMake cache/build trees. Record stage complete, exactly generated inventories and SHA-256 content manifest.
- Validate every input/checkpoint; upload validated short-lived same-run checkpoint and store exact-key cache for re-use if the later compile is canceled. No cache fallback keys.
- Apply time budget check that leaves **actual** headroom for bundle hashing/upload within the hosted 6h ceiling. If infeasible, stop after lightweight planning/small-fixture checks and redesign without another blind six-hour run. Do not fake 319 modules.

**Job C: generated native binding compilation/runtime producer**
- Restore and verify generated-source and OCCT SDK artifacts in a **fresh runner**, reconstruct CMake project in current paths and use a new native build directory; configure `-DOpenCASCADE_DIR` and locked CPython/toolchain paths; never reuse stale absolute CMake caches.
- Run `cmake --build ... --target OCP --parallel 4` against real C++ sources, no OCCT rebuild and no pywrap regeneration.
- Validate exactly one `OCP*.pyd` and required runtime OCCT DLLs. Seal final runtime and manifests including source-lock digest, stage identities, toolchain contract, hashes of every file, generated-src digest and binding-binary digest.
- Perform actual OCP import/CAD smoke. Publish final verified OCP runtime artifact, exact-input cache. Cache HIT must validate contents and source lock, not skip smoke.

**Job D: production Studio packaging/clearance**
- Consume only validated same-run final controlled-runtime artifact (not direct cross-run cache).
- Remove all opaque OCP-wheel binaries/libraries and verify none remain.
- Run full actual Qt GUI/QtPdf/OCP/Open3D package smoke, bidirectional controlled-runtime integrity, full redistribution/source/notice/forbidden Qt gates.
- Reach **zero** unresolved items and `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING` before producing unsigned installer. Keep legal review boundary explicit; do not label this public-release approval.

## Durable recovery, limits, and tests

- Every stage is a separately timed job, GitHub hosted; don't rely on `timeout-minutes:480` overriding six hours. Use appropriate <360 min job timeouts and leave setup/upload margin.
- Pinned full-SHA GitHub Actions upload/download/cache actions and strict read-back SHA/length checks. Artifact names include immutable phase/native-key/run identity; do not leak credentials, private scans, user paths or unrelated files.
- Cache exact native source lock + pywrap/OCP source + builder/validators + compiler/SDK + Python minor + stage schema, independent of unrelated Studio commits. Mismatches rebuild exact *affected stage* from preceding verified stage, never trust partial cache. No ambiguous cache restore.
- Add **testable jobs contract** (small synthetic OCCT+pywrap+extension fixtures and unit tests) proving phase isolation, tampered/missing content rejection, cache-key sensitivity, path portability and no job compiling a previous expensive phase.
- Do not generate tens of GB of local owner machine temp; all heavy native compilation on hosted GitHub runners. Preserve owner's currently working native Desktop `PackLab.exe`. Continue using local safe wrapper 40/4/2/8 GiB; no unrelated uv-cache prune or blanket AppData removal. Protected old content can remain deferred, no false 0-total-disk claim.
- **NO cold OCCT/pywrap re-execution is authorized by this R01 prompt.** Only if a subsequent explicit owner go-ahead approves the exact unavoidable phases may a single preflighted cold phase-split hosted run be launched. A completed job log does not preserve its intermediates. If it stops, retain verified stage checkpoints; never respin six-hour jobs blindly.
- After producer/installer cold run, perform a second real cache-HIT run with no pywrap rebuild and all validators & smoke. Record separate run URLs and artifact SHA.
- If no verified reusable complete checkpoint exists, **do not rebuild anything**: publish R0 recovery-inventory log, stop `OWNER_APPROVAL_REQUIRED_FOR_NATIVE_REBUILD`, record GitHub parity, and end `AWAITING_OWNER_DECISION`. No OwnerDev refresh is necessary for a read-only inventory. If a later owner-authorized downstream hosted phase remains blocked, use `BATCH_STOPPED_AT_PL-0350_V07_R01` and `AWAITING_MILESTONE_AUDIT`. PL-0351 forbidden until actual installer clears.
- If PL-0350 fully green, continue amended PL-0351 isolated fresh-Windows clean-installed-artifact/QtCore loader smoke. Then if PASS continue PL-0352..PL-0367 under existing ordered prompts/criteria. PL-0368 remains DEFERRED_POST_M17; never start M17, tag, release or sign.
- Codex logs must contain GitHub HTTPS links, actual tested/not-tested statuses and actual artifacts. No `C:\...` link handoff. Implementation and logs separate commits, same source authority synced. Do not modify ChatGPT-only `TASKS.md` or `CHATGPT_AUDIT` files.
