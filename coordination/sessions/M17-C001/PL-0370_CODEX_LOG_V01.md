---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M17-C001
version: 01
actor: CODEX
status: LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED
promptPath: coordination/sessions/M17-C001/PL-0370_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M17-C001/PL-0370_VALIDATION_CRITERIA_V01.md
startingCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
finalCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
---

# PackLab Codex Log V01 — M17-C001 — PL-0370

## Inputs read

- `AGENTS.md`, `TASKS.md`, M17 execution plan, PL-0370 prompt/criteria V01, dataset catalog, Codex log contract, and milestone batch protocol.
- Official YCB source index: https://ycb-benchmarks.s3.amazonaws.com/index.html
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/legalcode.en
- Owner's current instruction: no Kenya factory/scans exist; do not request data paths or photos; continue independently.

## Repository synchronization

- Local HEAD: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; `origin/main`: `db772e35f386fcba88fa6dbdd01d186959fa7162`; local 0 ahead/95 behind.
- `git fetch origin main` succeeded. Numerous owner/local modifications and untracked files are present. No fast-forward, commit, push, or Desktop refresh was performed to avoid overwriting or publishing owner work.

## Work performed

- Downloaded the official YCB mustard bottle and bleach cleanser 16k Google-scanner model archives and a bounded original Berkeley mustard-bottle RGB image archive; extracted two model packages and 30 original JPEGs (six per five source cameras).
- Added a local manifest with archive/member URLs and identities, sizes/hashes, source/license/attribution, frame selection, and image/model uncertainty notes.
- Added a fail-closed local YCB manifest validator. Full source and derived data are local only.

## Files changed

- `tools/datasets/extract_ycb_subset.py`
- `tools/datasets/validate_ycb_manifest.py`
- `coordination/sessions/M17-C001/PL-0370_CODEX_PROMPT_V01.md`
- `coordination/sessions/M17-C001/PL-0370_VALIDATION_CRITERIA_V01.md`
- Local-only files under `%LOCALAPPDATA%/PackLab/datasets/M17` (not in Git): three source archives, legal-code snapshot, README, extracted model files, selected JPEGs and manifests.

## Requirement / criteria evidence

- Local YCB manifest identity `packlab-m17-ycb-real-reference-v1`; 2 licensed model objects, 10 model files, and exactly 30 original JPEGs.
- Archive identities/sizes/SHA-256 values:
  - `006_mustard_bottle_google_16k.tgz`: 10,703,139 bytes, `992621f78a4fa6267da71418e530cd547bd066775da0242e578ddfb561d7cb5d`.
  - `021_bleach_cleanser_google_16k.tgz`: 10,668,522 bytes, `2d71162158f5b51089a08ea12180d47a6480f4ba986af0c887a93ad5fc867588`.
  - `006_mustard_bottle_berkeley_rgb_highres.tgz`: 1,431,508,625 bytes, `b67571728b8670003f9be620e48d4731afffb5a37f02a04938a7d3f8cc2c483c`.
- YCB index identifies the dataset as CC BY 4.0. Record-level validator binds each archive to its official direct URL and license/attribution fields.
- Photos and Google-scanner models are separate acquisitions; no camera calibration, photo-to-mesh registration, independently verified physical scale or Kenya origin is claimed.
- Source archive data total 1,452,929,028 bytes. Entire local M17 corpus currently uses 1,596,012,630 bytes across 335 files, outside Git.

## Validation commands

```text
py tools/datasets/validate_ycb_manifest.py "$env:LOCALAPPDATA/PackLab/datasets/M17/derived/ycb/manifest.json"
```

Expected: fail closed on invalid source URL/license, altered/missing archive or member digest/size, unsafe paths, incorrect image identity, missing attribution or overclaimed capture/measurement authority. Failure condition: nonzero exit or an invalid provenance record accepted. Actual: exit 0; manifest SHA-256 `5489d6b48c0b46dbadad45f1a8a099e7b7d8d599f17da6eca51e0348cd27a6cc`; result reported 2 model objects, 10 model files, 30 real photos, and 99,321,991 bytes in extracted references.

Expected grouped negative tests: malformed paths and metadata must fail; actual pytest/Tester not run, deferred to M17 end. No hosted Actions run.

## Negative / boundary / regression coverage

- Validator checks path containment and links, source archive official URL binding, archive bytes/hash, record bytes/hash, JPEG signature, exact object identities/counts, license/attribution and unknown calibration/authority. Current valid dataset passed.
- Automated negative fixture tests were added in the M17 grouped suite but were not executed in this task.

## Failures encountered and fixes

- No unresolved archive/extraction mismatch at final verification. Earlier generator extent failures are documented in PL-0369's log and were separate synthetic geometry corrections.

## Known limitations / unverified assumptions

- CC BY 4.0 covers the dataset copyright grant; it does not clear third-party trademarks, patents, or product trade dress. No external redistribution of the real corpus is authorized by this task.
- The source scanner/model scale is not independent physical ground truth. The real RGB images do not carry a bound camera pose/calibration or registration with supplied meshes.
- No private Kenya scan inputs or physical acceptance evidence exist.
- Comprehensive software tests, Tester and independent source/security reviews are pending at the M17 checkpoint.

## Security / privacy check

- Secrets/signing material committed: NO.
- Private Kenya scans/supplier data committed: NO.
- Full source archives and extracts remain outside Git. The local footprint is 1,596,012,630 bytes; no cleanup is claimed.

## Scope check

- No Kenya files were requested. No synthetic or YCB evidence was represented as Kenya field evidence.
- `TASKS.md` is locally dirty and was not rewritten for PL-0370 in this log.

## Commit and push evidence

- Implementation/evidence commit: none; owner-local dirty workspace preserved.
- Push: not attempted. Local checkout is 95 commits behind freshly fetched `origin/main`.
- Desktop sync/OwnerDev refresh: not attempted; preserving local state is required.

## Handoff

**LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED** — local real-reference corpus and manifest integrity check are present. PL-0370 remains unchecked until the milestone test/review checkpoint; future physical Kenya validation remains explicitly pending. Continue with PL-0371 and the remaining eligible M17 tasks.
