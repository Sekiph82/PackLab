---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: c4d10cd6
reviewedCommits: [5126bde0, c4d10cd6]
tasks: [PL-0369]
supersedes: CLAUDE_PEER_REVIEW_PL0369_V01.md (non-independent; disregarded)
respondsTo: CLAUDE_IMPLEMENTATION_LOG_PL0369_V02.md
reviewDate: 2026-11-10
verdict: CLAUDE_PEER_AUDITED_PASS
---

# Claude Independent Peer Review V02: PL-0369 public CI golden subset

The reviewer did not implement this work. This review is read-only: I made no source, tracker, fixture or Git changes.
`main` = `origin/main` = `c4d10cd6` (after fetch). The scope is `5126bde0` (subset, validator, tests, catalog) plus
`c4d10cd6` (CI data-safety allowlist and payload cap), which the coordinator added mid-review.

## Evidence

### 1. Subset is byte-identical to the full local dataset

I could see the full dataset at `%LOCALAPPDATA%\PackLab\datasets\M17\synthetic`. I compared the two with a script in
the scratchpad:

```
full manifest sha 3a37b55d8b93affdba73d23a39ba299c12053f433000a5911ac7f6e71ea3601b
subset top keys diff: ['golden_subset_of']
top-level non-sample fields equal: True
syn_bottle_pet_gloss_v01 bottle pet_gloss procedural_blender
syn_jerrycan_hdpe_matte_v01 jerrycan hdpe_matte procedural_blender
syn_jar_pet_clear_v02 jar pet_clear procedural_blender
syn_closure_pp_translucent_v01 closure pp_translucent procedural_blender
syn_trigger_spray_hdpe_matte_v03 trigger_spray hdpe_matte procedural_blender
syn_pump_pp_translucent_v02 pump pp_translucent procedural_blender
syn_tube_pet_gloss_v03 tube pet_gloss procedural_blender
syn_sachet_pet_clear_v01 sachet pet_clear procedural_blender
files referenced 24 files on disk 25 bytes 3614616
mismatches []
```

- All 8 sample records equal the full-manifest records exactly (dict equality).
- All 24 RGB/mask/PLY files are byte-equal to the full dataset and match their manifest SHA-256 values.
- The parent hash `3a37b55d…` matches the full manifest.
- The fixture covers one sample per family, and each of the 4 appearances appears twice.

### 2. Validator (CLI)

```
$ .venv/Scripts/python.exe tools/datasets/validate_packaging_dataset.py tests/fixtures/m17_golden_subset/manifest.json
{... "golden_subset": true, "manifest_sha256": "ed3da383...", "sample_count": 8}   exit=0
$ .venv/Scripts/python.exe tools/datasets/validate_packaging_dataset.py "$LOCALAPPDATA/PackLab/datasets/M17/synthetic/manifest.json"
{... "golden_subset": false, "manifest_sha256": "3a37b55d...", "sample_count": 96}  exit=0
```

### 3. Focused tests

```
$ QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/ci/test_packaging_dataset_manifest.py -q -p no:cacheprovider
25 passed, 3 skipped in 40.37s
```

The 3 skips are the existing symlink-privilege tests.

### 4. Reviewer's own mutations (temp copies; repository untouched)

| Mutation | Result |
|---|---|
| baseline subset | ACCEPTED (8, subset=True) |
| flip 1 byte in RGB PNG | REJECTED: file SHA-256 mismatch |
| flip 1 byte in mask PNG | REJECTED: file SHA-256 mismatch |
| flip 1 byte in PLY | REJECTED: PLY length/hash mismatch |
| remove `golden_subset_of` (8 samples) | REJECTED: unexpected sample count |
| `golden_subset_of: null` | REJECTED: parent record invalid |
| malformed parent sha | REJECTED: parent record invalid |
| parent `dataset_id` changed | REJECTED: parent record invalid |
| relabel jerrycan as bottle (duplicate family, distinct files) | REJECTED: family/appearance coverage incomplete |
| duplicate sample record (same files) | REJECTED: path collision |
| 9th sample appended | REJECTED: unexpected sample count |
| `fully_synthetic: false` | REJECTED |
| `measurement_authority` overstated | REJECTED |
| **parent sha = another well-formed 64-hex value** | **ACCEPTED** by the validator (see F1); the CI test rejects it |
| FULL 96 + `golden_subset_of` added | REJECTED: unexpected sample count |
| FULL with one sample removed | REJECTED: unexpected sample count |
| FULL baseline | ACCEPTED (96, subset=False) |

The full 96-sample path is unchanged. The subset branch is reached only when a structurally exact `golden_subset_of`
record is present, and then exactly 8 samples are required. An 8-sample manifest without the record cannot pass the
full path, and a 96-sample manifest with the record cannot pass the subset path. Every per-sample check still runs in
subset mode: hashes, PNG CRC/IHDR/mask coverage, PLY integrity and extent, camera intrinsics and pose, metric bands
and the tolerance band.

### 5. Git storage and content

```
$ git ls-files --eol tests/fixtures/m17_golden_subset   (summarised)
  16 i/-text w/-text attr/-text     (PNG)
   9 i/lf    w/lf    attr/-text     (manifest.json + 8 ASCII PLY)
$ git check-attr text -- tests/fixtures/m17_golden_subset/manifest.json
  text: unset
```

I checked the manifest, the PLYs and every PNG text/EXIF chunk for third-party names (YCB, Objectron, ABO), Kenya,
POVU, supplier, e-mail, user path and secret patterns:

- **Manifest:** "Kenya" and "supplier" appear only in disclaimers: "no physical or Kenya ground truth", "not supplier
  or physical tolerance evidence", and the internal-use scope string.
- **PLY headers:** they say `comment units meters; generated geometry; not physical CAD`.
- **PNG metadata:** it is Blender boilerplate only: `File=<untitled>`, render date/time, `Camera=virtual_camera`,
  `Scene=Scene`, and an empty eXIf.
- **Personal, third-party and secret data:** none found.

The repository is PUBLIC with no root license (`gh repo view` returns `licenseInfo: null`). So the subset does not
inherit any permissive license that would conflict with its restrictive `owner_internal_use_scope`.

### 6. Owner decision representation

`PL-0369_OWNER_DECISION_PUBLIC_GOLDEN_SUBSET_V01.md` records:

- the exact question ("May an 8-sample synthetic PL-0369 subset go in the public repo for CI?") and the owner's
  answer ("Yes, commit subset");
- the permitted scope: 8 PackLab-generated samples under `tests/fixtures/m17_golden_subset/`, for CI and software
  regression use;
- that it narrows the 2026-11-04 internal-use terms for this subset only, and acknowledges that the subset becomes
  publicly downloadable;
- that it grants no sale, sublicensing, marketing or trademark rights;
- that it leaves the full dataset's terms unchanged;
- "No formal legal review is claimed."

The content I inspected matches this scope (procedural only; no YCB, Objectron or ABO; no Kenya, supplier or physical
data). The record is not overstated. The catalog addition (`docs/datasets/M17_DATASET_CATALOG.md:47-49`) is
consistent with it.

### 7. CI data-safety follow-up `c4d10cd6`

- **Why it was needed.** Hosted run 42859298092 at 5126bde0 **failed** in the step "Guard tracked data and
  developer-runtime boundaries". The guard correctly blocked the new `.png` and `.ply` files as unapproved.
- **Allowlist entries.** `tools/ci/ci_safe_data_policy.json` gains 24 `approved_synthetic_fixtures` entries. My
  script checked each entry against both the working-tree file and the `HEAD` blob:
  `policy subset entries 24 tracked binaries 24 extra entries [] mismatch [] max size 305782`.
  Every approved path, byte size and SHA-256 matches the committed file. There are no extra or missing entries.
- **Cap change.** `maximum_manifested_payload_bytes` goes from 65536 to 524288 (`ci_safe_data_policy.json:138`).
  - The cap is read only inside `_matches_hash_manifest` (`tools/ci/ci_data_safety.py:257`). There it is an extra
    upper bound on a file that already has an exact path + size + SHA-256 allowlist entry.
  - Raising it cannot admit any file without its own pinned entry, and `ALWAYS_BLOCK` and private-path rules still
    run first. The change is narrow and acceptable. See F3 for the residual breadth.
- **Local guard and tests.**
  ```
  $ .venv/Scripts/python.exe -m tools.ci.ci_data_safety --repository . --tracked
  PACKLAB_CI_DATA_GUARD=PASS   exit=0
  $ ... --tracked --check-workflows --check-signing-secrets
  PACKLAB_CI_DATA_GUARD=PASS   exit=0
  $ QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/ci/test_ci_data_safety.py -q -p no:cacheprovider
  44 passed in 2.57s
  ```
  The log says "63 passed", but I observed 44 (see F4).

### 8. Hosted CI

| Run | SHA | Result |
|---|---|---|
| 42859298092 | 5126bde0 | **failure** (data-safety guard: unapproved PNG/PLY) |
| 42859677563 | c4d10cd6 | **success**: `PACKLAB_CI_DATA_GUARD=PASS`; `2612 passed, 16 skipped, 1 deselected` (3:43) |

2612 passed is +7 over the 2605 at c62220f2. That equals the 2 new subset tests plus 5 parametrised mutation cases, so
the subset tests ran on hosted Windows.

## Findings

| ID | Sev | Location | Finding | Disposition |
|---|---|---|---|---|
| F1 | P3 | `tools/datasets/validate_packaging_dataset.py:276` | The validator checks only that the parent `manifest_sha256` is 64-hex. Any other well-formed digest passes the CLI. The pin to `3a37b55d…` exists only in the CI test (`tests/ci/test_packaging_dataset_manifest.py:471,479`), and no tool verifies subset membership against the parent when the parent is present. | Non-blocking: CI enforces the pin, and I verified membership manually (§1). Optional follow-up: a `--parent` check mode. |
| F2 | P3 | `tools/datasets/run_benchmark_regression.py:194` | The regression report keeps the same `dataset_id` and does not expose `golden_subset`. A subset run is distinguishable from a full run only by its counts. | Non-blocking; suggest adding `golden_subset` to the report. |
| F3 | P3 | `tools/ci/ci_safe_data_policy.json:138` | The cap is global: future allowlisted fixtures or assets of up to 512 KiB are also admitted. A per-entry or per-tree cap would be narrower. | Acceptable; every file still needs an exact hash pin. |
| F4 | P3 | `coordination/sessions/M17-C001/CLAUDE_IMPLEMENTATION_LOG_PL0369_V02.md:45` | The log claims `tests/ci/test_ci_data_safety.py` "63 passed". I collected and passed 44. | Correct the evidence when the tracker is updated; the tests pass either way. |
| F5 | P2 | `docs/datasets/M17_DATASET_CATALOG.md:11-17`, `tools/datasets/extract_ycb_subset.py` | YCB real-reference archives are still not verified locally (earlier F14). | Non-blocking for PL-0369 (see judgement); record it as a limit. |
| F6 | P3 | `TASKS.md:10`, `TASKS.md:750` | The tracker still shows PL-0369 as `OWNER_DECISION_REQUIRED` / `IMPLEMENTED_REVIEW_PENDING` with older SHAs. | The coordinator should update it with this evidence. |

No P0 or P1 findings.

Earlier finding F13 ("CI golden dataset is a contract fixture only") is **resolved**. CI now validates real generated
samples that are byte-pinned to the full dataset, and it runs the segmentation regression harness on their masks.

## Judgement

**Contract for synthetic/public scope.** PL-0369 is "small redistributable synthetic/public golden dataset for CI",
read with PL-0369_VALIDATION_CRITERIA_V04. The subset meets it:

- **Small:** 25 files, 3.6 MB.
- **Redistributable:** within the recorded owner decision, with no third-party content.
- **CI-usable:** it is validated and harness-exercised on hosted Windows.
- **Metric ground truth:** PLY meshes in metres, simulated mm dimensions, tolerance and metric bands.
- **Provenance:** generator path, version, seed, `procedural_blender`, and the parent hash.
- **Negative cases:** the existing manifest tests plus 5 new subset mutations, and my own mutations above.
- **Explicit labels:** `fully_synthetic`, `physical_measurements_present: false`, `NONPHYSICAL_SOFTWARE_TEST_ONLY`,
  `mm_simulated`.

**YCB.** The phrase "license-verified real-world reference inputs where suitable" belongs to the PL-0375+ execution
contracts, not PL-0369's own line. PL-0369's title allows "synthetic/public". Criterion 3 of V04 applies to
*downloaded* source objects. None are present or committed, and the catalog's documented fallback
(`M17_DATASET_CATALOG.md:17`) is to use the synthetic fixture when no verified archive is available. The task can
therefore pass without YCB, provided the limit stays recorded and no real-world reference claim is made. None is made.

**Weakening of the full-dataset path.** None found (§4). The guard change is hash-pinned per file (§7).

**Owner decision.** It is accurately represented, scoped to this subset, and claims no legal review.

**Limits that stay open elsewhere:** YCB verification, physical, Kenya and factory validation (PL-0370 external),
and any SAM 2.1 or real reconstruction accuracy.

## Verdict

**PL-0369: CLAUDE_PEER_AUDITED_PASS** (synthetic/public CI scope), at source `c4d10cd6`. Hosted Windows Python
Quality run 42859677563 SUCCESS. The P3 follow-ups F1–F4 and F6, and the P2 limit F5, are non-blocking.
