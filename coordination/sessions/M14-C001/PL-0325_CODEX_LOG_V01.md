# PL-0325 - Codex Implementation Log V01

Task: **Create deterministic Blender scene-generation script from PackLab project data**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0325_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0325_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes M14-C001-R02, including sequential continuation through PL-0331; PL-0325 was the active child after PL-0324. The tracker was not edited. M15+ remains unauthorized.
- Read the M14-C001-R02 continuation prompt and criteria, live `TASKS.md`, and PL-0324/PL-0325 prompt and criteria before PL-0325 implementation. The M13-C001-R02 final audit, M09 physical-validation owner decision and ADR-0005 were read as part of the PL-0324 batch pre-read and rechecked for this handoff.
- Starting synchronized SHA: `6ba532c2fc515c4b419112bdad70b5019b4fa97e`; execution branch `codex/m13-c001-pl0297`; push ref `origin/main`. Protected Desktop checkout was not touched.
- Implementation/evidence commit: `88b4ac8fe123feb1a44dbba07357939e28a7e072` (`Add bounded Blender scene package generator`). After publication, local `HEAD`, fetched `origin/main`, and GitHub `main` matched at this SHA.

## Implementation

Added `core/src/packlab_core/blender_scene_package.py` and focused tests in `tests/core/test_blender_scene_package.py`.

The immutable package generator emits canonical, versioned JSON plus one fixed static Blender Python validator. The manifest pins the exact Design Model, CAD export/GLB manifest and BREP geometry digests, component material-project/library revisions, per-component material/PBR/PCR visual metadata, and supplied Label Zone/placement/mapping/artwork/assignment revisions. Artwork references bind their project-relative paths, lengths and digests to the exact accepted artwork bytes and placement chain.

Asset paths must be canonical project-relative POSIX paths; absolute, drive-qualified, traversal, backslash and non-canonical paths reject. Per-asset, total-asset, manifest, object, material and artwork bounds are enforced. The Blender runner validates the versioned envelope, body digest, path containment, asset size/digest and fixed count limits. User values are JSON data; the static runner does not execute manifest strings or embed them as Python. The package excludes ambient absolute paths and makes no source geometry mutation.

Physical accuracy stays `DEFERRED_OWNER_VALIDATION`; scale/unit provenance is preserved. Manifest authority flags deny Design Model/BREP mutation, inferred physical accuracy, manufacturing suitability, certified material or regulatory approval. This package does not build or render a scene and proves no print fit, physical accuracy, manufacturing suitability, material certification or regulatory approval.

A new artwork provenance test initially exposed an invalid sort-key lookup in the generated artwork record. The record now includes its exact zone and variant keys; the final focused and full locked suites pass with that correction.

Files changed in the implementation commit:

- `core/src/packlab_core/blender_scene_package.py`
- `tests/core/test_blender_scene_package.py`

No dependency/lockfile, tracker, audit verdict, Blender executable, private evidence, later-child or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest tests/core/test_blender_scene_package.py -q` | Determinism, exact model/export/material/artwork provenance, source immutability, unsafe paths, injection/ambient identity, contract and object/material/artwork bounds; any failure blocks. | PASS: 11 passed. |
| `uv run --locked pytest -q` | Locked full repository suite passes. | PASS: 1,827 passed, 6 skipped, 1 deselected in 176.96s; two existing duplicate ZIP-name warnings. |
| Changed-file Ruff and format | `uv run ruff check core/src/packlab_core/blender_scene_package.py tests/core/test_blender_scene_package.py`; `uv run ruff format --check ...` | PASS: all checks passed; both files formatted. |
| Targeted mypy | `uv run mypy --follow-imports=silent core/src/packlab_core/blender_scene_package.py` | PASS: no issues in the changed module. A normal import-following invocation also reported two pre-existing errors in untouched `core/src/packlab_core/calibration/marker_detection.py` (lines 112 and 140); no changed-file errors. |
| Compile and dependency lock | `uv run python -m compileall -q core/src/packlab_core/blender_scene_package.py tests/core/test_blender_scene_package.py`; `uv lock --check` | PASS: compile succeeded; 78 packages resolved with no lock change. |
| Real Blender package smoke | Installed approved Blender, background/factory startup, auto-execution disabled; run the generated fixed validator against a fixture asset and then a manifest with modified body but stale digest. | PASS: Blender 5.2.2 LTS, build hash `d13f752e3b9c`, branch `blender-v5.2-release`, build date `2026-09-15`; valid package emitted `PACKLAB_SCENE_PACKAGE_VALID 5.2.2 LTS`. Tampered package emitted `manifest_digest_invalid` and no success marker. Blender's process exit code is not used as the Python validation signal. |
| Protected scope, privacy and whitespace review | No `TASKS.md`, dependency, audit, later-task or private/local-path changes; no runtime network/download; `git diff --cached --check`. | PASS. Package bytes contain no ambient workspace path; the only executable text is the fixed validator. |
| Remote preflight and implementation publication | `git fetch origin main`; `git rev-list --left-right --count HEAD...origin/main`; push `HEAD:main`; compare `HEAD`, `origin/main`, and `git ls-remote origin refs/heads/main`. | PASS: pre-push divergence `0 0`; implementation SHA `88b4ac8fe123feb1a44dbba07357939e28a7e072` is visible and equal on local `HEAD`, `origin/main`, and GitHub `main`. |

## Limitations

- Blender validation covers the static package envelope, safe path containment and digest-bound assets only. PL-0325 does not construct, import, render or export a scene; those behaviors remain for later authorized children.
- The real Blender process reports a Python exception while returning exit code 0 for the deliberately tampered manifest; the smoke checks the explicit `manifest_digest_invalid` diagnostic and absence of the success marker.
- Unfiltered mypy traversal remains red only because of the two recorded errors in the untouched calibration marker module; changed-module analysis passes with imported-module traversal silenced.
- mm_unverified stays physically unverified, and all physical, print, manufacturing, certification and regulatory limitations remain in force.

## Handoff

PL-0325 V01 implementation/evidence is builder-green and published. Its matching log is being published separately, followed by the authorized original-master and R02 continuation index updates. No independent audit verdict is claimed.

READY_FOR_INDEPENDENT_AUDIT
