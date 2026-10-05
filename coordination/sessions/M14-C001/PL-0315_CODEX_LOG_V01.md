# PL-0315 - Codex Implementation Log V01

Task: **Import SVG/PNG artwork and map it non-destructively to a Label Zone**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0315_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0315_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes M14-C001-R02: PL-0313 V02 followed by PL-0314 through PL-0331; actor `CODEX`. The tracker was not edited.
- Re-read the PL-0314 V01 prompt/criteria/log, M13 final audit, M09 physical-validation deferral, ADR-0005, and PL-0315 prompt/criteria before implementation.
- Starting synchronized SHA: `0af845af237cea62a7287010435620693294fcdd`; clean managed worktree, branch `codex/m13-c001-pl0297`, push target `origin/main`. The Desktop owner checkout remains untouched.
- Implementation/evidence commit: `d79186126a233b37c3ec898daa87ae72a7141a49` (`Add bounded label artwork ingest and mapping`), pushed to `origin/main`.

## Implementation

Added `core/src/packlab_core/label_artwork.py` with separate immutable asset and mapping revision contracts. Ingest accepts bounded in-memory bytes or a local path, validates content, and binds exact raw-byte SHA-256, media type, size and intrinsic dimensions. The supplied path and filename are never included in the asset revision or serialized metadata; symlinks, non-files, unreadable files and oversized content fail with path-independent errors.

SVG validation requires well-formed UTF-8 XML with an SVG root and finite positive viewBox or dimensions. It bounds document bytes, nodes and depth, and rejects DTD/entities, scripts, embedded image/use/foreign content, event handlers, href/src, CSS `url()`/`@import`, XML stylesheet instructions, and non-finite dimensions. PNG validation checks signature, chunk order/CRC, IHDR, supported non-interlaced 8-bit color modes, bounded dimensions/pixels/chunks, IDAT decompression size and stream integrity; animation is rejected.

Artwork mapping pins asset digest/revision, exact Label Zone and placement revision, fit mode, normalized target rectangle, source-artwork crop rectangle, scale and translation. CONTAIN, COVER and STRETCH are deterministic. Artwork remains presentation-only and cannot modify Design Model, CAD BREP or Label Zone authority; replacement artwork creates a different presentation revision while reusing the same exact zone placement.

Files changed:

- `core/src/packlab_core/label_artwork.py`
- `tests/core/test_label_artwork.py`

No dependency, lockfile, tracker, audit artifact, later child, or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_label_artwork.py tests/core/test_label_zone.py tests/core/test_label_zone_placement.py` | SVG/PNG ingest and Label Zone mapping regressions pass; unsafe, malformed, oversized or stale inputs fail closed. | PASS: 47 passed in 1.52s. Covers SVG and PNG digests, malformed/remote/active SVG, PNG CRC/structure/dimension limits, byte limits, private-path omission, CONTAIN/COVER/STRETCH, replacement independence, and unsupported input/fit. |
| `uv run --locked pytest -q` | Locked repository suite passes; any failure blocks this child. | PASS: 1,701 passed, 6 skipped, 1 deselected in 173.63s. Two duplicate ZIP-name warnings in existing PackScan/container validation tests. |
| `uv run --locked ruff check core/src/packlab_core/label_artwork.py tests/core/test_label_artwork.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/label_artwork.py tests/core/test_label_artwork.py` | Changed files are formatted. | PASS: both files formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/label_artwork.py` | Changed source passes targeted typing. | PASS: no issues in 1 source file. |
| `uv run --locked python -m compileall -q core/src/packlab_core/label_artwork.py tests/core/test_label_artwork.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff --exit-code -- TASKS.md pyproject.toml uv.lock` | No dependency/lockfile or tracker change. | PASS: 78 packages resolved; no diff. |
| `git diff --check`; changed-file privacy/security/scope scan | No whitespace, private path persistence, network fetch, or scope leakage. | PASS. No runtime network APIs, subprocess use, private artwork fixtures, saved source path/name, or out-of-scope files. Remote URLs occur only in negative synthetic SVG tests. |

An initial targeted mypy pass found constructor/translation typing issues and they were corrected. Final focused, full and static checks passed. PNG decode is bounded before decompression output is accepted.

## Limitations

- This child validates and describes artwork metadata; it does not render, certify, or physically print artwork.
- Raster PNG support is intentionally limited to bounded non-interlaced 8-bit PNG color modes. SVG external references, active content and unsupported dimensions are rejected.
- Mapping coordinates are unitless normalized UV presentation metadata, not mm or geometry authority. Print fit and physical validation remain unverified.

## Handoff

PL-0315 V01 implementation/evidence is builder-green and published. Its matching log is published separately and ends with the required marker. Continue the authorized batch at PL-0316 after log/index publication and remote parity verification; no independent audit verdict is claimed here.

READY_FOR_INDEPENDENT_AUDIT
