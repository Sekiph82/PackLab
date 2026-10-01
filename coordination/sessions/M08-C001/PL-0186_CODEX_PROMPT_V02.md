# PL-0186 — Codex Work Order V02

Task: **Implement owner-approved SAM 2.1 Hiera Base+ local PyTorch segmentation backend**

Repository:
https://github.com/Sekiph82/PackLab

Branch:
`main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Owner decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

Mandatory contract pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V02.md

## Canonical synchronization gate

Before any material work:

1. `git fetch origin main --prune`
2. inspect `git status --porcelain`
3. inspect `git rev-list --left-right --count HEAD...origin/main`
4. fast-forward only when safe

Do not reset, rebase, force-push, destructively clean, overwrite owner work, or use a sibling worktree to bypass a dirty/diverged canonical checkout.

The live tracker must authorize:
- Current Milestone: M08
- Current Sprint: M08-C001
- Current Task: PL-0186 V02
- Current Task Status: READY
- Required Actor: CODEX
- PL-0184 and PL-0185 accepted
- PL-0187+ and M09 unauthorized

Otherwise stop `TASK_STATE_MISMATCH`.

Do not edit `TASKS.md`, ADR-0004, ChatGPT criteria/audits, accepted predecessor evidence or later-task files.

## Frozen owner decision

Implement **Meta SAM 2.1 Hiera Base+** behind PackLab's existing `SegmentationBackend` boundary.

Frozen identity:

- upstream repo: https://github.com/facebookresearch/sam2
- reviewed source revision: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- repository source license: Apache-2.0
- checkpoint: `sam2.1_hiera_base_plus.pt`
- config: `configs/sam2.1/sam2.1_hiera_b+.yaml`
- official checkpoint source:
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt
- inference: local PyTorch only
- hosted API: forbidden
- CUDA: optional/capability-probed
- CPU: functional fallback, no performance guarantee
- automatic application-time checkpoint download: forbidden

## Architecture

SAM-specific implementation must stay behind a PackLab-owned adapter/runtime seam.

Required shape:

```text
PackLab SegmentationRequest
        ↓
SAM21BasePlusBackend
        ↓
local runtime adapter / capability probe
        ↓
SAM 2.1 image predictor
        ↓
normalized source-pixel mask
        ↓
SegmentationResult / MaskArtifact
```

Downstream consumers must not import `sam2`, `torch` or model-specific types.

Prefer a boundary that keeps heavyweight ML/runtime dependencies isolated from PackLab domain truth. If an explicit local ML runtime/environment seam is cleaner than inserting platform/GPU-specific wheels into the canonical PackLab app environment, use that architecture and document it. Do not add an unreviewed hosted service.

## Checkpoint acquisition and provenance

ADR-0004 authorizes explicit acquisition of the official checkpoint for implementation/validation.

Rules:

- obtain it only from the approved Meta URL;
- do not commit the checkpoint to Git;
- do not add silent runtime auto-download;
- compute and record SHA-256 and byte size after acquisition;
- persist configured expected hash in PackLab-owned provenance/config/evidence;
- fail closed on missing checkpoint or hash mismatch;
- do not accept arbitrary lookalike filenames as the selected checkpoint.

Record the actual local source path only in non-portable diagnostics if necessary. Project artifacts must use portable identities, not machine-absolute paths.

## Runtime

Use local PyTorch.

Upstream requires/recommends:
- Python >= 3.10
- PyTorch >= 2.5.1
- matching torchvision
- CUDA toolkit only when using the CUDA path
- WSL is strongly recommended upstream for Windows

PackLab itself uses Python 3.12.

Do not blindly mutate canonical dependencies. First determine and document the safest PackLab runtime boundary. Record exact actual versions/builds used.

Capability report must distinguish at least:
- backend configured/unconfigured;
- runtime import/executable available/unavailable;
- model/config present/missing;
- checkpoint hash verified/mismatched;
- CPU available;
- CUDA available/unavailable;
- supported prompt modes.

Native Windows versus WSL must be a probed/reportable runtime fact, not an assumption.

## Functional scope

Implement only PL-0186.

Minimum supported public behavior:
- point prompt segmentation;
- box prompt segmentation;
- source-image pixel coordinate normalization;
- deterministic model/checkpoint/runtime provenance;
- bounded confidence/output normalization where applicable.

Automatic image mask generation may be exposed only if implemented safely and capability-probed.

Do not implement PL-0187 PackLab post-processing policy, PL-0188 manual correction UI, PL-0189 invalidation changes or PL-0190 lifting.

## Failure behavior

Fail closed on:
- missing runtime;
- missing config;
- missing checkpoint;
- checkpoint hash mismatch;
- unsupported prompt mode;
- invalid prompt coordinates;
- malformed model output;
- output/source dimension mismatch without a valid transform;
- non-finite invalid confidence/score values;
- runtime exception or device failure.

No failure path may emit a valid-looking `MaskArtifact`.

Never modify RAW_CAPTURE/source image bytes.

## Tests

Add focused public-boundary tests using fake/local runtime seams so the suite does not require GPU/network/model installation.

Mandatory:
- exact model/config/checkpoint identity;
- expected checkpoint hash verification;
- hash mismatch rejection;
- missing runtime/model/config/checkpoint;
- no auto-download/network fallback;
- point prompt;
- box prompt;
- coordinate transform round trip to source pixels;
- malformed output rejection;
- source immutability;
- CPU vs CUDA capability reporting;
- backend replacement/downstream isolation;
- PL-0184 and PL-0185 regressions.

If a real SAM 2.1 run is performed, use only public/synthetic imagery and record it separately as native E2 evidence. Do not use private scans.

## Dependency and license evidence

Update only the minimal PackLab-owned dependency/runtime evidence needed by the implementation.

Record:
- exact SAM 2 source revision/package form;
- PyTorch version/build;
- torchvision version/build;
- CUDA/runtime version if used;
- checkpoint source;
- checkpoint byte size;
- checkpoint SHA-256;
- relevant LICENSE/NOTICE provenance.

Do not claim that repository Apache-2.0 automatically describes every transitive PyTorch/CUDA binary. Preserve the component-level license boundary.

## Validation

Run:
- dedicated PL-0186 tests;
- PL-0184 / PL-0185 regressions;
- exact locked full pytest suite;
- Ruff;
- format check;
- targeted/relevant mypy;
- compileall;
- `git diff --check`;
- protected-file/scope checks;
- dependency/lock review;
- privacy/secrets/signing review;
- generated/binary review;
- remote visibility/freshness checks.

Known unrelated pre-existing lint/type debt may be reported only if unchanged.

## Publication

Use separate commits:

1. implementation/evidence commit(s);
2. log-only commit containing:
   https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CODEX_LOG_V02.md

The log must include:
- synchronized starting SHA;
- implementation SHA(s);
- exact architecture/runtime boundary chosen;
- exact dependency/runtime versions;
- checkpoint official URL, local byte size and SHA-256;
- capability report;
- focused/full/static validation;
- changed files;
- limitations;
- explicit statement that PL-0187+ was not started.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Independent ChatGPT audit is required before PL-0187.
