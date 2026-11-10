# PL-0424 Codex Prompt V01 — Deterministic Reconstruction Anomaly Proposals

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; PL-0424 follows the bounded PL-0423 evidence/proposal boundary.

## Objective

Add a deterministic, explainable anomaly detector that surfaces likely reconstruction defects before parametric fitting, using PackLab's existing geometry-statistics and reconstruction-confidence records.

## Mandatory pre-reads

- `core/src/packlab_core/geometry_statistics.py`
- `core/src/packlab_core/reconstruction_confidence.py`
- `core/src/packlab_core/pre_reconstruction_qa.py`
- `core/src/packlab_core/captured_geometry_fit_gate.py`
- `docs/implementation/PL-0420_LEARNED_FEATURE_RECOGNITION_RESEARCH.md`
- `coordination/sessions/M19-C005/PL-0423_CODEX_PROMPT_V01.md`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

## Allowed scope

- Add `core/src/packlab_core/reconstruction_anomaly.py` to transform existing diagnostic records into a deterministic, content-digest-bound finding list.
- Add synthetic/local tests in `tests/core/test_reconstruction_anomaly.py`.
- Update root `TASKS.md`, matching log and local job record for verified results.

## Hard constraints

- Findings are review suggestions only. Do not change/remove geometry, fill holes, modify confidence reports, promote Scan Master, modify measurements/calibration, or authorize physical accuracy/mold use.
- Keep source revision/digest binding exact. Use explicit allow-listed anomaly codes and fixed deterministic rules; missing evidence must be reported as incomplete rather than a clean result.
- Serialize only identifiers, counts, allow-listed codes and digests; never raw geometry, image/scan payloads, file paths, supplier data or owner data.
- No model/SDK/checkpoint download, installation, inference or activation. No generated repair proposal.
- Keep the owner's free-to-use/private-source preference distinct from model licensing; any future model remains gated on documented terms, pinned identity and specific owner acceptance.
- Zero GitHub Actions/paid CI, no PR, no source push to `main`, no native OCCT/OCP or Installer builds, and no hosted/device/release claim.

## Validation and handoff

Run the exact focused local suite in `PL-0424_VALIDATION_CRITERIA_V01.md` using the project `.venv`, then `git diff --check`. Record expected/actual results, boundaries and cleanup/publication facts in `PL-0424_CODEX_LOG_V01.md`. Continue the dependency-ready queue after local evidence is recorded.
