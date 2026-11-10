# PL-0420 Codex Prompt V01 — Learned Packaging Feature Recognition Research

Date: 2026-10-22  
Owner authorization: PL-0420 is the next dependency-ready research task in the delegated PackLab queue.

## Objective

Research a safe, testable approach for recognizing bottle/jerrycan body, shoulder, base, neck and handle regions from PackLab's captured imagery and reconstructed geometry. Deliver a bounded architecture recommendation without enabling a learned model.

## Mandatory pre-reads

- `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`
- `docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`
- `docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md`

## Allowed scope

- Read existing PackLab segmentation, feature, package-family and reconstruction contracts.
- Use official upstream repositories, official model cards/licenses, and primary research papers for external claims.
- Add `docs/implementation/PL-0420_LEARNED_FEATURE_RECOGNITION_RESEARCH.md` with methods, evidence, limitations, licensing/deployment implications, and an implementation-ready recommendation.
- Write this matching prompt, criteria and Codex log.
- Update the live tracker and PL-0420 job metadata for the actual local research result.

## Hard constraints

- Research only: no model SDK/package installation, checkpoint download, inference, training, or model enablement.
- No private PackScan, supplier, Kenya, or owner imagery may be used or uploaded.
- Learned suggestions remain proposals with human confirmation; they cannot alter Scan Master, measurements, calibration, capture coverage or authoritative geometry.
- Preserve the owner's free-to-use/private-source product preference as a deployment constraint. Do not treat it as acceptance of any model license or as proof a downloadable executable can hide its implementation/weights.
- Zero GitHub Actions/paid CI, no PR, and no source push to `main`. No native OCCT/OCP or Installer builds.
- Do not modify historical audit evidence or claim hosted/device/audit/release acceptance.

## Validation and handoff

Verify every research claim against cited primary sources, verify local architecture references by file, run `git diff --check`, and record exact outcomes and unresolved owner/legal gates in `PL-0420_CODEX_LOG_V01.md`. Continue only with dependency-ready tasks; do not infer model approval from the research report.
