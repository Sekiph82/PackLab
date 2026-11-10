# PL-0422 Codex Prompt V01 — Parametric Section Placement Proposal Contract

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; PL-0422 follows the locally validated PL-0421 confirmation boundary.

## Objective

Add an optional, backend-neutral contract for proposing axial placements of existing parametric profile zones. A proposal is non-authoritative until a user explicitly confirms one candidate against the exact current fitted-profile and zone revisions.

## Mandatory pre-reads

- `core/src/packlab_core/design_profile_zones.py`
- `core/src/packlab_core/design_profile_fit.py`
- `docs/implementation/PL-0420_LEARNED_FEATURE_RECOGNITION_RESEARCH.md`
- `coordination/sessions/M19-C003/PL-0421_CODEX_PROMPT_V01.md`
- `coordination/sessions/M19-C003/PL-0421_VALIDATION_CRITERIA_V01.md`
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`

## Allowed scope

- Add `core/src/packlab_core/profile_zone_proposal.py` with safe request, candidate, suggestion, provenance and backend protocol records.
- Add an explicit acceptance function which validates the exact source fit/zone revisions and routes the chosen placement through `override_design_profile_zones`, returning an immutable manual revision and separate digest-bound acceptance record.
- Add deterministic fake-backend tests in `tests/core/test_profile_zone_proposal.py`.
- Update root `TASKS.md`, this task's matching log, and local job metadata with verified local evidence.

## Hard constraints

- No AI package/checkpoint installation, download, inference, training, or activation. No network/backend integration.
- A suggestion must not mutate existing profile fit or zones. Acceptance must be explicit, bind to exact source revisions and the suggestion digest, and preserve feature identity, coordinate units, scan-master binding and deferred physical accuracy. The result must remain `MANUAL_OVERRIDE` / `review_required` through the existing authority path.
- Do not serialize profile samples, scan bytes, paths, supplier data or owner data. Use safe IDs, scalar axial coordinates and content digests only.
- No suggestion or accepted placement changes Scan Master, measurement, calibration, physical-accuracy validation, or mold-use authority.
- The owner's free-to-use/private-source product preference does not accept any model license. Keep specific code/checkpoint and distribution/runtime terms, pinned identity/hash, and owner license acceptance as open activation gates.
- Zero GitHub Actions/paid CI, no PR, no source push to `main`, and no native OCCT/OCP or Installer builds. No hosted/device/release claim.

## Validation and handoff

Run exactly the focused tests in `PL-0422_VALIDATION_CRITERIA_V01.md` with the project `.venv`, plus `git diff --check`. Record initial failures/fixes, exact results, and cleanup/publication facts in `PL-0422_CODEX_LOG_V01.md`. Continue the dependency-ready queue after recording locally verified evidence.
