# PL-0423 Codex Prompt V01 — Bounded Fit-Parameter Optimization Proposal

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; PL-0423 follows locally validated immutable proposal tasks PL-0421 and PL-0422.

## Objective

Add a backend-neutral optimization proposal contract for numeric Design Model parameters. Proposals must bind to the exact Design Model and Scan Master revisions, respect explicit measured-dimension target/tolerance bounds, and stay under a declared Scan Master deviation budget. User confirmation creates only a successor Design Model revision that remains physically unvalidated and unauthorized for mold use.

## Mandatory pre-reads

- `core/src/packlab_core/design_model.py`
- `core/src/packlab_core/design_dimensions.py`
- `core/src/packlab_core/design_deviation_report.py`
- `core/src/packlab_core/scan_master.py`
- `docs/implementation/PL-0420_LEARNED_FEATURE_RECOGNITION_RESEARCH.md`
- `coordination/sessions/M19-C003/PL-0421_CODEX_PROMPT_V01.md`
- `coordination/sessions/M19-C004/PL-0422_CODEX_PROMPT_V01.md`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

## Allowed scope

- Add `core/src/packlab_core/dimension_fit_proposal.py` with explicit measured-dimension constraints, deviation budget, candidate, proposal provenance and backend protocol.
- Add explicit acceptance of one candidate by constructing an immutable `DesignModelRevision` successor through PackLab's existing revision API.
- Add focused deterministic fake-backend tests in `tests/core/test_dimension_fit_proposal.py`.
- Update root `TASKS.md`, matching log and local job record for verified results.

## Hard constraints

- No model/optimizer SDK, checkpoint, training, download, inference or backend integration. Fake backend only.
- Require exact source model revision, fitted Scan Master revision and geometry digest. Require candidate parameter IDs to exist and be numeric. Require every output to lie within explicit user-declared measured target ± tolerance and within the deviation budget. Any deviations are estimates/constraint evidence only, not manufacturing tolerances or physical-accuracy validation.
- A backend-reported candidate deviation and evaluation digest are untrusted proposal metadata; acceptance does not prove that candidate geometry was regenerated or independently compared to the Scan Master. Preserve `DEFERRED_OWNER_VALIDATION` and require downstream geometric recomputation/review before any physical or production use.
- Candidate and suggestion serialization contain only safe IDs, scalar values and content digests. No geometry, scans, paths, supplier data or owner data.
- Confirmation creates a new model revision with unchanged Scan Master ancestry, `DEFERRED_OWNER_VALIDATION`, and `mold_use_authorized=False`. No automatic mutation or physical-accuracy promotion.
- Keep the owner's free-to-use/private-source preference distinct from code/checkpoint licensing. The model activation gate stays open.
- Zero GitHub Actions/paid CI, no PR, no source push to `main`, no native OCCT/OCP or Installer builds, and no hosted/device/release claim.

## Validation and handoff

Read this prompt's mandatory references. Run exactly the focused pytest specified in `PL-0423_VALIDATION_CRITERIA_V01.md` with the project `.venv` and `git diff --check`. Record exact outcomes, limitations and cleanup/publication facts in `PL-0423_CODEX_LOG_V01.md`. Continue the queue only after recording locally verified evidence.
