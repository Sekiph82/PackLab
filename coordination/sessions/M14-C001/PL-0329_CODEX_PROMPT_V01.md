# PL-0329 - Codex Prompt V01

Task: **Render front/three-quarter/back standard views**
Milestone: **M14 - Labels, Materials & Rendering**
Cycle: **M14-C001**

## M14 non-negotiable Blender/render rules

- Read live root TASKS.md, M13 final audit, M09 physical-validation deferral, ADR-0005, and the exact predecessor child prompt/criteria before implementation.
- Blender is an external executable capability, not a PackLab-bundled binary. No runtime auto-download, installer fetch, hidden network dependency, or committed Blender binary is allowed.
- Exact Design Model/CAD/Label Zone/artwork/material source revisions remain authority; render/mesh/image outputs are derived presentation artifacts.
- RELATIVE/reconstruction_units never silently becomes millimetres. mm_unverified remains physically unverified.
- Render success never implies mold, manufacturing, package-fit, material certification, artwork print approval, regulatory approval, or physical accuracy.
- Material/PBR/PCR values are visual/design metadata only unless separately authorized by explicit external certification evidence.
- Generated scripts/manifests must be deterministic and privacy-safe; do not encode ambient absolute paths or machine/user identity into canonical identities.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- Each child gets an implementation/evidence commit and a distinct log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- M15+ is unauthorized.

## Required implementation

Implement ordered headless rendering of standard front, three-quarter and back views using the accepted camera presets, with one manifest tying all outputs to the exact same scene/source revisions and render settings.

## Required validation

Cover at minimum: three required views; unique camera IDs/transforms; non-empty/non-clipped renders; consistent dimensions/settings; per-output digests; shared scene revision; deterministic ordering; partial-failure cleanup; no false physical/render certification.

For Blender-dependent children, run the real approved headless executable when the child requires it. Unit fakes may supplement but may not substitute for a mandatory real capability/render/export smoke. Run focused predecessor/regression tests, the locked full repository suite, changed-file Ruff/format, targeted mypy/compile checks where applicable, dependency/lockfile check, scope/privacy/security review, and remote publication verification.

Stop on any real capability failure, dependency/license/privacy issue, source-authority ambiguity, or missing real Blender requirement. Do not fabricate PASS evidence.

## Handoff

Publish the implementation/evidence commit, then publish `coordination/sessions/M14-C001/PL-0329_CODEX_LOG_V01.md` in a separate log-only commit. Record exact changed files, commands/results, Blender capability facts where applicable, limitations, final local/origin/GitHub parity, and stop at this child if any mandatory criterion cannot be proved.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
