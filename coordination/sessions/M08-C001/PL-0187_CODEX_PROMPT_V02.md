# PL-0187 — Codex Work Order V02

Task: **Implement deterministic PackLab-owned mask post-processing**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V02.md

## Authorization gate

Before material work:

1. `git fetch origin main --prune`
2. inspect `git status --porcelain`
3. inspect `git rev-list --left-right --count HEAD...origin/main`
4. fast-forward only when safe

The live tracker must authorize:
- Current Milestone: M08
- Current Sprint: M08-C001
- Current Task: PL-0187 V02
- Current Task Status: READY
- Required Actor: CODEX
- PL-0186 independently accepted
- PL-0188+ and M09 unauthorized

Otherwise stop `TASK_STATE_MISMATCH`.

Do not edit `TASKS.md`, owner ADRs, ChatGPT audits/criteria, accepted predecessor evidence or later-task files.

## Frozen scope

Implement a **PackLab-owned deterministic post-processing pipeline** for valid parent masks.

PL-0187 owns only:

1. bounded hole filling;
2. bounded edge cleanup;
3. bounded small-component removal.

Do not implement:
- manual correction UI;
- downstream mask invalidation orchestration;
- mask-to-3D lifting;
- geometry cleanup/fitting;
- model/runtime/checkpoint changes;
- aggressive smoothing/resampling.

PL-0186 raw SAM output must remain reproducible and untouched.

## Required artifact model

Input:
`MaskArtifact parent`

Output:
a **new** post-processed `MaskArtifact` / revision derived from that parent.

Never mutate parent mask content or replace the original raw model artifact.

The child provenance/revision identity must preserve at minimum:

- parent artifact ID;
- parent mask revision;
- parent mask digest;
- source image asset ID/digest;
- source dimensions;
- source coordinate transform;
- post-processing pipeline ID/version;
- exact normalized parameter set;
- before/after foreground pixel counts;
- deterministic output mask digest;
- deterministic child revision identity;
- created timestamp as non-identity metadata if current contracts require it.

Same parent + same parameters + same pipeline version must produce the same mask/revision identity.

## Algorithm requirements

### Hole filling

Fill only enclosed background regions whose pixel area is within an explicit maximum threshold.

Requirements:
- image boundary-connected background is not a hole;
- threshold behavior is exact and tested;
- threshold zero means no hole filling;
- no dimension change.

### Small-component removal

Remove foreground connected components whose pixel area falls within the selected removal rule.

Define and document connectivity explicitly, for example 4-connectivity or 8-connectivity. Do not leave connectivity implicit.

Threshold behavior must be exact and tested.

### Edge cleanup

Use a conservative deterministic pixel-domain rule.

The rule must be:
- explicitly defined;
- bounded;
- versioned;
- incapable of arbitrary iterative erosion/dilation beyond configured bounds;
- tested on edge-touching and thin legitimate features.

Do not convert PL-0187 into visual smoothing. Preservation of packaging silhouette evidence has priority over cosmetic masks.

If a conservative edge-cleanup operation cannot be justified under the existing contract, implement the smallest safe bounded rule and document its limitation rather than inventing aggressive cleanup.

## Parameter contract

Create an immutable/versioned parameter object or equivalent.

Parameters must:
- reject bool-as-int ambiguity where relevant;
- reject negative values;
- reject non-finite numeric values;
- have safe maximum bounds tied to image dimensions or explicit project constants;
- serialize deterministically;
- participate in revision/provenance identity.

No environment-dependent or random behavior.

## Coordinate and authority invariants

Post-processing operates on the existing mask grid.

Do not:
- resize;
- resample;
- change source dimensions;
- change top-left origin;
- change source image identity;
- alter RAW_CAPTURE/source bytes.

The resulting artifact remains a derived mask, not geometry or metrology authority.

## Parent reproducibility

The parent raw-model mask must remain independently serializable and reproducible after child creation.

If the pipeline needs raster bytes, consume them read-only.

Do not overwrite `mask_asset_id` in a way that makes parent/child indistinguishable. Use a deterministic child identity/path convention compatible with PackLab project rules.

## Tests

Add focused tests for:

- same input/params -> same output digest/revision;
- different parameter -> different provenance/revision when output or processing contract changes;
- parent artifact unchanged;
- source bytes unchanged;
- hole fill threshold below/at/above;
- boundary-connected background not filled;
- small foreground components below/at/above threshold;
- selected connectivity semantics;
- empty mask;
- full mask;
- edge-touching object;
- thin legitimate feature under edge cleanup;
- invalid/negative/oversized parameters;
- dimension mismatch/rejection;
- parent ancestry serialized into child provenance;
- PL-0184/PL-0186 regressions.

Use public/synthetic fixtures only.

## Dependency rule

Prefer dependency-free PackLab-owned implementation unless an existing reviewed dependency is already appropriate.

Do not add OpenCV/SciPy/skimage or another dependency merely to avoid implementing bounded binary-mask operations unless there is a documented and reviewed reason.

No model/checkpoint/runtime download.

## Validation

Run:

- dedicated PL-0187 focused tests;
- PL-0184/PL-0186 segmentation regressions;
- exact locked full pytest suite;
- Ruff;
- format check;
- targeted/relevant mypy;
- compileall;
- `git diff --check`;
- protected-file/scope review;
- dependency/license review;
- privacy/secrets/signing review;
- generated/binary review;
- remote visibility/freshness checks.

Known unrelated repository debt may be reported only if unchanged.

## Publication

Create separate commits:

1. implementation/evidence commit(s);
2. log-only commit:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CODEX_LOG_V02.md

The log must include:
- synchronized starting SHA;
- implementation SHA(s);
- exact pipeline version;
- exact connectivity and threshold semantics;
- parameter bounds;
- child revision/ancestry identity strategy;
- focused/full/static results;
- changed files;
- limitations;
- explicit statement that PL-0188+ and M09 were not started.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Independent ChatGPT audit is required before PL-0188.
