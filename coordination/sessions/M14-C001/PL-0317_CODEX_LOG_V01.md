# PL-0317 - Codex Implementation Log V01

Task: **Export label-dieline SVG with scale-verification marks**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0317_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0317_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes `M14-C001-R02`: PL-0313 V02 followed by PL-0314 through PL-0331; actor `CODEX`. The tracker was not edited.
- Read live `TASKS.md`, the exact PL-0316 predecessor prompt/criteria, M13 R02 final audit, M09 physical-validation deferral, ADR-0005, and this PL-0317 prompt/criteria before implementation.
- Starting synchronized SHA: `31aa0e84637e77f10e4854931fdc5ea3800ff541`; worktree clean on `codex/m13-c001-pl0297`, push target `origin/main`. The Desktop owner checkout remains untouched.
- Implementation/evidence commit: `c929af191b98597e42e01b51422740b11c127884` (`Export label dielines as verified SVG intent`), pushed to `origin/main`.

## Implementation

Added `core/src/packlab_core/label_dieline_svg.py` with immutable `LabelDielineSvgExport` metadata and a deterministic SVG exporter. Export requires an exact placement whose Label Zone is `METRIC_UNVERIFIED` / `mm_unverified`, a matching source Design Model/BREP/digest/parent/placement binding, and a source dieline with the PL-0314 print-intent safe and bleed boundaries attached. RELATIVE, stale/mismatched provenance, and missing print-intent inputs fail closed.

The SVG declares numerical `width`/`height` in `mm` and an explicit numeric viewBox. It emits vector `<path>` geometry in distinct source-outline, safe-margin, bleed, and scale-verification layers; embeds source/current dieline, zone, placement, Design Model, BREP revision/digest, analysis/region, and metric-binding provenance; and includes physical-unverified and not-print-ready text plus machine-readable false certification/fit/readiness fields. Output bytes and revision ID are deterministic and SHA-256 bound.

The verification strip is placed separately below the bleed outline and includes an exactly 10 mm design-coordinate bar with endpoint ticks. It is expressly labeled `mm_unverified`; it does not establish printer scaling or physical accuracy. SVG width/height include this strip and its spacing in addition to the bleed extents.

Files changed:

- `core/src/packlab_core/label_dieline_svg.py`
- `tests/core/test_label_dieline_svg.py`

No dependency, lockfile, tracker, audit artifact, later child, or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_label_dieline_svg.py tests/core/test_label_dieline_print_intent.py tests/core/test_label_metric_surface_binding.py` | SVG, print-intent, and metric-binding regressions pass; RELATIVE, stale, or missing print-intent input fails closed. | PASS: 30 passed in 14.88s. Covers XML parse, vector-only paths, mm dimensions/viewBox, safe/bleed paths, known 10 mm bar, source revisions/digest, deterministic output, unverified disclaimer, RELATIVE rejection, and binding mismatch. |
| `uv run --locked pytest -q` | Locked repository suite passes; any failure blocks this child. | PASS: 1,717 passed, 6 skipped, 1 deselected in 264.17s. Two existing duplicate ZIP-name warnings in container-validation tests. |
| `uv run --locked ruff check core/src/packlab_core/label_dieline_svg.py tests/core/test_label_dieline_svg.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/label_dieline_svg.py tests/core/test_label_dieline_svg.py` | Changed files are formatted. | PASS: both files formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/label_dieline_svg.py` | Changed source passes targeted typing. | PASS: no issues in 1 source file. |
| `uv run --locked python -m compileall -q core/src/packlab_core/label_dieline_svg.py tests/core/test_label_dieline_svg.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff --exit-code -- TASKS.md pyproject.toml uv.lock` | No dependency/lockfile or tracker change. | PASS: 78 packages resolved; no diff. |
| `git diff --check`; changed-file security/scope review | No whitespace or scope leakage; no network or private source data. | PASS. Only the two scoped files changed; no runtime network/subprocess, private fixtures, or absolute source-path output. |
| Push/parity check (`git fetch origin main`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git ls-remote origin refs/heads/main`, status) | Published implementation matches canonical GitHub `main`. | PASS at implementation commit `c929af191b98597e42e01b51422740b11c127884`; local, fetched origin, and live ref equal; worktree clean. |

## Limitations

- `mm_unverified` is preserved in the SVG and metadata. The scale bar represents a nominal 10 mm coordinate span only; actual printer scaling and physical fit remain unverified.
- Export is available only for a matching PL-0314 print-intent dieline and exact metric-unverified zone placement. RELATIVE input is never converted or promoted to millimetres.
- No printer certification, manufacturing, mold, regulatory, or production-readiness claim is made. The SVG is explicitly marked not print-ready.

## Handoff

PL-0317 V01 implementation/evidence is builder-green and published. Its matching log is published separately and ends with the required marker. No independent audit verdict is claimed. Continue at PL-0318 only after this child log/index publication and remote parity verification.

READY_FOR_INDEPENDENT_AUDIT
