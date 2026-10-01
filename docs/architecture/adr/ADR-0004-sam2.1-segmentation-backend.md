# ADR-0004 — SAM 2.1 Base+ as PackLab V1 Segmentation Backend

- Status: **ACCEPTED**
- Owner approval date: **2026-10-01**
- Scope: **M08 / PL-0186 production segmentation backend selection**
- Owner decision: **APPROVED**

## Decision

PackLab V1 selects **Meta SAM 2.1 Hiera Base+** as the production segmentation model behind the PackLab-owned `SegmentationBackend` contract.

Frozen model identity:

- Upstream repository: https://github.com/facebookresearch/sam2
- Reviewed upstream commit: `2b90b9f5ceec907a1c18123530e92e794ad901a4`
- Repository license: **Apache License 2.0**
- Checkpoint file: `sam2.1_hiera_base_plus.pt`
- Config file: `configs/sam2.1/sam2.1_hiera_b+.yaml`
- Official checkpoint source:
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt

The official upstream README identifies SAM 2.1 Hiera Base+ as one of the released SAM 2.1 checkpoints and documents image prompting plus automatic mask generation.

## Runtime decision

- Runtime is **local PyTorch** only.
- No hosted segmentation API is authorized for V1.
- CUDA acceleration may be used when capability probing confirms a compatible local runtime.
- CPU execution is an accepted functional fallback, but no CPU performance guarantee is implied.
- PackLab must probe runtime/device capabilities rather than assume CUDA, native Windows or WSL behavior.
- Upstream currently recommends Python >=3.10, PyTorch >=2.5.1 and matching torchvision; PackLab itself remains Python 3.12.
- Exact PyTorch, torchvision, SAM 2 code/package and accelerator artifacts used by PL-0186 must be recorded in implementation evidence and the dependency/license register before acceptance.

## Checkpoint provenance rule

The production checkpoint must come **only from the official Meta/Facebook public source above**.

Before PackLab treats the checkpoint as available:

1. obtain the checkpoint explicitly, never through silent runtime auto-download;
2. compute its SHA-256 locally;
3. record filename, source URL, byte size and SHA-256 in PackLab provenance/evidence;
4. fail closed if the configured checkpoint is missing or its recorded hash does not match;
5. never commit the checkpoint binary to Git.

The owner approval authorizes explicit acquisition for implementation/validation. It does **not** authorize automatic application-time downloads.

## Architectural boundary

SAM 2.1 remains replaceable behind:

`SegmentationBackend -> SegmentationResult -> MaskArtifact`

No downstream object-extraction or geometry code may import SAM-specific APIs.

SAM-specific code belongs only inside the selected backend adapter/runtime boundary.

Every emitted `MaskArtifact` must preserve:

- source image asset identity and digest;
- source pixel coordinate semantics;
- model/checkpoint identity;
- checkpoint SHA-256;
- runtime/device provenance;
- prompt provenance;
- transforms between model input and source pixels.

RAW_CAPTURE remains immutable.

## Authorized capability set for PL-0186

PL-0186 may implement and expose only capabilities actually proven through the adapter, including:

- point prompts;
- box prompts;
- automatic image mask generation where supported by the selected local runtime;
- bounded batch/image execution where implemented safely.

Capabilities must be probed and reported. Unsupported or unavailable capabilities must fail closed rather than be fabricated.

## License boundary

The reviewed SAM 2 repository license at the frozen upstream revision is Apache-2.0.

This owner decision is a project governance decision, not legal advice or a final binary-distribution opinion. Release packaging must still inventory:

- the exact SAM 2 source/package revision;
- the checkpoint artifact;
- PyTorch/torchvision package/build notices and native libraries;
- CUDA/runtime components if shipped;
- all required LICENSE/NOTICE files.

## Rejected alternatives for this V1 decision

- SAM 3 / SAM 3.1 is not selected for PL-0186.
- Hosted segmentation services are not selected.
- SAM 3D Objects is not selected as the 2D segmentation backend.
- Synthetic PL-0185 baselines remain benchmark-contract evidence only.

## Consequence for M08

The prior `NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER` is resolved at the owner-decision layer.

ChatGPT may authorize **PL-0186 V02** for Codex under this ADR. PL-0187+ and M09 remain unauthorized until PL-0186 independently passes audit.
