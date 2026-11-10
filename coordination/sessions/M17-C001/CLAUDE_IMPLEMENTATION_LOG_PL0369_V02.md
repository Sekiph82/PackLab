---
coordinationSchema: packlab-coordination/v1
artifactType: claude-implementation-log
cycleId: M17-C001
version: 02
actor: CLAUDE_CODE
status: IMPLEMENTED_REVIEW_PENDING
tasks: [PL-0369]
respondsTo: CLAUDE_PEER_REVIEW_PL0370_0374_V01.md (PL-0369 CHANGES_REQUIRED)
---

# Claude Implementation Log V02 — PL-0369 public CI golden subset

Review finding: CI had no real golden data, only an in-test fixture; YCB archives are not available locally.

## Change

- Owner decision (2026-11-10): `PL-0369_OWNER_DECISION_PUBLIC_GOLDEN_SUBSET_V01.md` — an 8-sample synthetic subset
  may be committed to the public repo for CI.
- `tests/fixtures/m17_golden_subset/`: 8 samples copied byte-for-byte from the regenerated dataset (manifest sha256
  `3a37b55d...`), one per family, each appearance twice; 25 files, 3,614,616 bytes; `-text` in `.gitattributes`.
- `tools/datasets/validate_packaging_dataset.py`: optional `golden_subset_of` record (exact keys, parent dataset ID,
  parent manifest SHA-256, decision path). Subset requires 8 samples covering all families with each appearance
  exactly twice; every per-sample check (hashes, PNG/PLY integrity, camera, bands, tolerance) still applies. The
  full 96-sample path is unchanged.
- Tests: subset validates and is pinned to the full manifest hash; harness runs PackLab mask post-processing on the
  real subset masks (16 PASS, 48 NOT_EVALUATED, PARTIAL_PASS); five parent-record/coverage mutations are rejected.

## Evidence

`pytest tests/ci/test_packaging_dataset_manifest.py` → 25 passed, 3 skipped (symlink privilege). Full local dataset
still validates (96 samples). ruff/format/mypy clean.

## Limits

YCB real-reference archives remain unverified locally and are not part of the CI golden data; the subset is synthetic
only and carries no physical or Kenya authority.

## Addendum — CI data-safety guard (hosted run 42859298092 FAILED)

The repository's `tools/ci/ci_data_safety.py` guard correctly blocked the new `.png`/`.ply` files as unapproved
sensitive payloads. Remediation: each of the 24 subset binaries is registered by exact path, byte size and SHA-256
in `tools/ci/ci_safe_data_policy.json` (`approved_synthetic_fixtures`), and `maximum_manifested_payload_bytes` was
raised from 65,536 to 524,288 because the largest render is 305,782 bytes. Every approved file still has to match
its pinned hash and size. Local guard: `PACKLAB_CI_DATA_GUARD=PASS`; `tests/ci/test_ci_data_safety.py` 63 passed.
