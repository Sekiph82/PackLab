---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M17-C001
version: 02
actor: CODEX
status: IMPLEMENTATION_COMPLETE_VALIDATION_PENDING
promptPath: coordination/sessions/M17-C001/PL-0370_CODEX_PROMPT_V02.md
criteriaPath: coordination/sessions/M17-C001/PL-0370_VALIDATION_CRITERIA_V02.md
startingCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
finalCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
---

# PL-0370 Codex Log V02 — Pinned YCB provenance and safe extraction

## Inputs and synchronization

- Read `AGENTS.md`, `TASKS.md`, M17 execution plan, PL-0370 prompt/criteria V02, V01 log, YCB catalog, code/log contracts, and the independent M17 source/security findings.
- Public `origin/main` fetched at `db772e35f386fcba88fa6dbdd01d186959fa7162`; local starting/final HEAD `f8745047063aca6c17378ecb33604e6e1e5b5f02`, 0 ahead/95 behind, dirty with owner-local changes. No fast-forward, commit, push, Actions, or Desktop sync.

## Work performed / files changed

- Added `tools/datasets/ycb_source_identity.py` pinning the three reviewed official URLs, exact archive byte counts and SHA-256 digests.
- Hardened `tools/datasets/extract_ycb_subset.py`: archive path/reparse/containment and pinned digest checks before read; atomic temporary member copy with expected size, fsync and exclusive link publication; no final partial file on interruption; safe atomic manifest write that rejects linked destinations.
- Hardened `tools/datasets/validate_ycb_manifest.py`: pinned archive identities and source URL, linked manifest/source rejection, and one-pass verification that selected extracted file bytes/hashes match their recorded source archive members.
- Added regression test sources in `tests/ci/test_packaging_dataset_manifest.py` for archive and manifest symlinks, interrupted extraction cleanup, archive member byte binding, and pinned identity.
- Both extractor/validator support direct-script invocation and module import. An initial direct validator invocation failed because the shared identity module was imported only through `tools`; a fallback for direct script execution was added. A second run revealed Windows path canonicalization mismatch between the visible `%LOCALAPPDATA%` alias and its resolved backing path; relative manifest path is now captured before resolving the dataset root.

## Data evidence

The full YCB corpus remains outside Git under `%LOCALAPPDATA%/PackLab/datasets/M17`. Pinned sources:

- `006_mustard_bottle_google_16k.tgz`: 10,703,139 bytes, `992621f78a4fa6267da71418e530cd547bd066775da0242e578ddfb561d7cb5d`.
- `021_bleach_cleanser_google_16k.tgz`: 10,668,522 bytes, `2d71162158f5b51089a08ea12180d47a6480f4ba986af0c887a93ad5fc867588`.
- `006_mustard_bottle_berkeley_rgb_highres.tgz`: 1,431,508,625 bytes, `b67571728b8670003f9be620e48d4731afffb5a37f02a04938a7d3f8cc2c483c`.

The manifest still says 2 scanner model objects/10 model files and 30 original JPEGs. Photos and meshes remain separate acquisitions; no physical scale, photo/model registration, Kenya origin, trademark or trade-dress clearance is claimed.

## Post-remediation artifact validation

```text
.venv\Scripts\python.exe tools\datasets\validate_ycb_manifest.py "$env:LOCALAPPDATA/PackLab/datasets/M17/derived/ycb/manifest.json"
```

Expected: reject changed archive identity or any extracted record that differs from its exact archive member; validate all selected references and provenance. Failure condition: nonzero exit or any changed/incorrect record accepted. Actual: exit 0; `derived_bytes=99,321,991`, 2 model objects, 10 model files, 30 real photos; manifest SHA-256 `5489d6b48c0b46dbadad45f1a8a099e7b7d8d599f17da6eca51e0348cd27a6cc`.

## Test/review status and known limits

- Before the review fixes, one consolidated pytest run reported 147 passed, 17 failed, 1 skipped; after two fixture/diagnostic fixes a second grouped rerun reported 142 passed. The latter excluded OCP-dependent modules because `OCP` is unavailable. These runs predate the current YCB remediation and new security regression test source.
- Post-remediation regression tests **NOT RUN**. Do not treat the earlier suite as validation of these new changes. Broad M17 Tester already ran twice; no more broad run is authorized in this child.
- The new member-binding validator reads/decompresses each pinned source archive during validation; it passed on this local corpus. The extractor still has no test here against malicious OS-level concurrent parent-directory swaps.
- Independent reviewers are rechecking the remediated diff. PL-0370 remains unchecked pending final-source regression validation and review closure.

## Final root-path remediation checkpoint

- Added `_resolve_dataset_root`: compare the requested absolute path with the canonical `%LOCALAPPDATA%/PackLab/datasets/M17` path using normalized lexical paths, inspect each of the dedicated suffix components for symlink/junction before resolving, then require the resolved target to be the dedicated root and outside Git.
- Added `test_ycb_dataset_root_symlink_is_rejected_before_resolution`. The fixture skips only if the host cannot create a directory symlink. It has **not** been run, in accordance with the owner’s milestone-batched test instruction; do not claim this regression is passing.
- Independent source and security reviewers inspected the actual latest source and both reported PASS for the previous root-path P2 issue. They confirmed the symlink case in source; they did not execute tests. Windows junction execution is not directly covered by a created fixture, while the implementation checks `Path.is_junction()` when available.
- Re-ran only the task-specific pinned YCB artifact validator after the root-path change. Actual exit 0: 2 model objects, 10 model files, 30 real photos, `derived_bytes=99,321,991`, manifest SHA-256 `5489d6b48c0b46dbadad45f1a8a099e7b7d8d599f17da6eca51e0348cd27a6cc`.
- The latest grouped pytest result remains the earlier 142 passed / 0 failed / 0 skipped run, which predates this final root-path change. It is not evidence for this final source. Keep PL-0370 incomplete until an authorized consolidated validation covers the current code.
- Both reviewers report no concrete remaining source/security finding within the requested root-path scope. Full M17 acceptance, CI/hosted evidence, physical Kenya validation, and publication remain unclaimed.

## Security/privacy and publication

- No secrets, supplier files or Kenya scans were added. Entire YCB corpus remains outside Git; only compact source identity values and code/test source are local workspace changes.
- Upstream CC BY 4.0 remains authoritative; PackLab internal-use scope does not relicense it. No formal legal review is claimed.
- Dirty local tree is 95 commits behind fetched origin; no commit/push/Desktop refresh.

**LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED** — local pinned source/member validator passes; new security regression tests remain unrun. Keep PL-0370 incomplete until final-source tests/reviews close.
