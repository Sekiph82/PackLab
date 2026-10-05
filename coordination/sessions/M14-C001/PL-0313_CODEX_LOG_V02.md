# PL-0313 - Codex Implementation Log V02

Task: **Metric Label Surface Binding + deterministic mm_unverified dieline**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_CRITERIA_V02.md

## Authorization and synchronization

- Live root `TASKS.md` authorized M14-C001-R02: PL-0313 V02 followed by PL-0314 through PL-0331; status `CHANGES_REQUIRED`; required actor `CODEX`. The tracker was not edited.
- Read the R02 continuation master/criteria, PL-0313 V02 prompt/criteria, M14 partial audit V02, accepted PL-0312 V02 prompt/criteria/audit/implementation contract, PL-0310 and PL-0311 prompts/contracts/audits, PL-0313 V01 blocker log, M13 final audit, M09 physical-validation deferral, ADR-0005, coordination/audit/batch protocols, and publication skill.
- Starting synchronized SHA: `a9314b609971e0058bf27c427d5f1620a9176e03`. The clean managed worktree fast-forwarded safely from `3ba09d5308f78d7e446a724bc4a077bf87e62c25`; the Desktop owner checkout was preserved.
- Implementation/evidence commit: `ac286de71e16372f6eddc8289460c905cfa1f355` (`Add exact metric label surface bindings`). It is visible on live GitHub `main`.
- PL-0310 through PL-0312 accepted source/evidence remains unchanged. M15+ was not started.

## V01 blocker resolution and implementation

PL-0313 V01 correctly stopped because normalized Label Zone UV had no accepted mapping to exact CAD surface dimensions or wrap seam/unroll semantics. R02/PL-0313 V02 explicitly authorized an immutable Label Metric Surface Binding for exact planar rectangular and cylindrical wrap surfaces. This implementation applies only that frozen resolution.

Added `core/src/packlab_core/label_metric_surface_binding.py` with deterministic immutable binding/dieline values and identity checks. The binding pins exact zone and placement revisions, Design Model revision, BREP revision/digest, parent authority, PL-0312 analysis revision/region, supported mapping mode, metric dimensions, mapping parameters, and limitations. The metric gate rejects RELATIVE/reconstruction_units and only permits METRIC_UNVERIFIED/mm_unverified output.

Host resolution recomputes the exact PL-0312 analysis and exact BREP sampling, then matches the selected canonical candidate support evidence. A private runtime-only face handle is retained only during that resolution; it is excluded from candidate equality, serialized data and binding/dieline identity. Zero or multiple matching host faces fail closed. No native face index, topology traversal ID, mesh ID, preview, raster, or whole-solid bounding box is persisted or used as the metric host.

- FRONT/BACK: accepts one exact planar face with one wire, four straight edges and four rectangular canonical-frame corners; only the compatible accepted normal/frame is supported. Other or ambiguous trims fail closed.
- WRAP: accepts an exact full cylindrical host with +Z axis and the explicit +Y seam/+Y-to-+X orientation. Radius, full host circumference and axial extent come from exact CAD geometry. Normalized partial zones map to exact arc length; unsupported/partial host trims fail closed.
- Dielines preserve deterministic ordered vertices, explicit winding, dimensions/extents, source mapping metadata, `mm_unverified`, and physical/print/manufacturing/regulatory limitations.

Files changed in the implementation commit:

- `core/src/packlab_core/cad_adapter.py` — private transient host handle on runtime surface samples, not serialized.
- `core/src/packlab_core/label_metric_surface_binding.py` — exact supported binding and dieline contracts.
- `tests/core/test_label_metric_surface_binding.py` — positive, negative, provenance, determinism and immutability coverage.

No dependency, lockfile, tracker, accepted M13 mapper, accepted PL-0310→0312 source, or audit artifact was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_label_metric_surface_binding.py tests/core/test_cad_label_surface_analysis.py tests/core/test_label_zone.py tests/core/test_label_zone_placement.py` | Metric binding and accepted predecessor regressions pass; authority or geometry ambiguity fails. | PASS: 55 passed in 5.54s. Covers FRONT/BACK dimensions and orientation, normalized sub-rectangle, cylinder partial/full circumference arc length, relative/stale rejection, non-rectangular trim, non-cylinder rejection, ambiguous face resolution, deterministic reordering/IDs, serialization and source immutability. |
| `uv run --locked pytest -q` | Locked complete repository suite passes; any unrelated failure must be identified and reported. | PASS: 1,669 passed, 6 skipped, 1 deselected in 116.11s. Two pre-existing duplicate ZIP-name warnings in PackScan/container validation tests. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py core/src/packlab_core/label_metric_surface_binding.py tests/core/test_label_metric_surface_binding.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py core/src/packlab_core/label_metric_surface_binding.py tests/core/test_label_metric_surface_binding.py` | Changed files are formatted. | PASS: all three files formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py core/src/packlab_core/label_metric_surface_binding.py` | Changed source has no targeted type errors. | PASS: no issues in 2 source files. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py core/src/packlab_core/label_metric_surface_binding.py tests/core/test_label_metric_surface_binding.py` | Changed source/tests compile. | PASS. |
| `uv lock --check`; `git diff --exit-code -- TASKS.md pyproject.toml uv.lock` | Lock and protected tracker are unchanged. | PASS: 78 packages resolved; no lock/dependency/tracker diff. |
| `git diff --check`; changed-file privacy/security/scope scan | No whitespace errors, secrets/private paths/network fetches, unauthorized identity, or out-of-scope edits. | PASS. Only the three listed implementation/test paths changed in implementation commit; no secret, private evidence, runtime network/download, tracker edit, PL-0314+ implementation, or M15+ work. |
| `git fetch origin main`; compare `HEAD`, `origin/main`, `git ls-remote origin refs/heads/main` | Published implementation is visible and local/origin/live-main are equal. | PASS: all three refs `ac286de71e16372f6eddc8289460c905cfa1f355`. |

During development, a generic OCP shape needed conversion to a typed edge before curve inspection, and the accepted cylinder seam had to be checked via the exact cylinder coordinate frame. Both were corrected; the final focused and full suites are green.

## Limitations

- Numerical geometry remains `mm_unverified`; physical accuracy validation is deferred and print fit is not verified.
- No safe margin/bleed, shrink/material/manufacturing compensation, mold, manufacturing or regulatory authorization is included.
- Planar mapping requires a single exact rectangular canonical-frame face. Wrap mapping currently accepts a full cylindrical host and normalized partial label domains; non-cylindrical/freeform and partial host trims fail closed.
- PL-0313 does not establish physical fit or certification.

## Handoff

PL-0313 V02 implementation/evidence is builder-green and published. Its separate V02 log is published in a log-only commit. The authorized batch continues with PL-0314 under its frozen prompt and criteria; no audit verdict is claimed here.

READY_FOR_INDEPENDENT_AUDIT
