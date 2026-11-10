# PL-0369 — Codex Prompt V04

Task: **Create a bounded, attributable real-plus-synthetic packaging validation dataset foundation**  
Milestone: **M17 — Validation, Benchmarking & Reliability**  
Cycle: **M17-C001**

V04 incorporates the owner's 2026-11-04 direction to create realistic local data autonomously, keep it outside Git, use licensed real packaging data where practical, and supplement it with physically coherent reproducible synthetic data. It supersedes V03 scope. V01–V03 remain immutable history. The owner explicitly states that Kenya is not yet built and no Kenya scan dataset exists; do not request it.

## Authority and scope

- Root `TASKS.md` authorizes PL-0369. Keep it the only live status tracker.
- Build a small manifest/catalog and reproducible generator/validator for the M17 packaging dataset. The local dataset resides under `%LOCALAPPDATA%/PackLab/datasets/M17`, never in Git.
- Use the official YCB Object and Model Set as an initial real-world reference if the selected assets and archive-specific terms/hash are verified. Preserve source files and attribution. No trademarks or product trade dress are licensed by CC BY; retain such source data locally and do not publish it.
- Generate synthetic 3D packages/renderings for bottle, jerrycan, jar, closure, trigger spray, pump, tube and sachet families. Cover HDPE/PET/PP appearance assumptions, opaque/matte/gloss/clear/translucent presentation, multiple calibrated virtual views, lighting, reflections, shadows, controlled image noise/distortion, and deterministic synthetic dimensional/tolerance metadata. Do not label any simulation as a physical measurement.
- Record source URL, exact license and attribution, local file hash/size, real/synthetic origin, dimensional authority, camera model/pose/intrinsics, render assumptions, tool version, seed, and known limits. License uncertainty fails closed for redistribution.
- Dataset-specific internal-use terms authorized by the owner cover PackLab development/CI and owner-controlled design-office and future Kenya-factory use. They grant no outside reuse, sublicense, sale, marketing, or repository-wide rights. Do not claim formal legal review.
- No Kenya data exists. Real-world public references and synthetic fixtures may validate software paths; neither substitutes for future physical Kenya acceptance.
- Do not alter old audit attribution or claim independent/hosted/device/release acceptance. Do not publish while the working tree diverges from canonical `origin/main`, while local owner changes are present, or while zero-CI/zero-paid-CI policy applies.

## Validation timing

- Add meaningful tests for dataset manifest validation and software consumers, but defer milestone-wide pytest, Tester, Ruff/mypy batch, and consolidated audits until the M17 end checkpoint after PL-0395 or all M17 tasks have reached evidenced implemented/blocked states. Run only a narrow test early if required to diagnose an observed implementation failure or if the owner explicitly requests that scope.
- Validate actual data artifacts with source checksums, archive structure inspection, manifest integrity checks, and a bounded Blender generation run as task acceptance evidence; do not represent these operational integrity checks as the M17 software test batch.
- Keep PL-0369 open until the planned M17 batch and advisory source/security review are complete. Keep PL-0370 and PL-0371–PL-0374 separate for the private local data and benchmark/metrics/harness work.

