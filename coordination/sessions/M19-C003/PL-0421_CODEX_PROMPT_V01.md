# PL-0421 Codex Prompt V01 — Package-Family Suggestion Contract

Date: 2026-10-22  
Owner authorization: PL-0421 is the next dependency-ready PackLab task; the owner delegated offline implementation and task sequencing.

## Objective

Add a backend-neutral, non-authoritative package-family suggestion contract with an explicit human-acceptance seam. Preserve the existing PackagingAsset family/provenance as the only authoritative library state.

## Mandatory pre-reads

- `core/src/packlab_core/packaging_asset.py`
- `core/src/packlab_core/design_model.py` (`PackageFamily` enum)
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`
- `docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md` for generated-output authority boundary principles

## Allowed scope

- Add a backend-neutral request, candidate, suggestion record, and `PackageFamilySuggestionBackend` protocol in `core/src/packlab_core/package_family_suggestion.py`.
- Add explicit owner-confirmation logic that returns an immutable PackagingAsset successor and a separate acceptance record; no automatic mutation or model execution.
- Add focused tests in `tests/core/test_package_family_suggestion.py`.
- Update root `TASKS.md`, the matching log, and a local task job record for actual evidence.

## Hard constraints

- Contract and deterministic fake-backend tests only. No real AI/model integration, dependency installation, checkpoint download, inference, or runtime enablement.
- Suggestion output must remain separate from authoritative `PackagingAsset` values until an explicit acceptance call. Acceptance must record user-confirmed `USER_DECLARED` provenance and bind to the exact asset revision and suggestion digest.
- No image/scan bytes, paths, supplier information, or owner data in suggestion serialization. Use content digests and safe identifiers only.
- Respect the owner's free-to-use/private-source deployment preference, but do not treat it as acceptance of any model license. Record the model gate as open.
- Zero GitHub Actions/paid CI, no PR, and no source push to `main`. No native OCCT/OCP or Installer builds.
- No `TASKS.md` claim of model availability, hosted verification, independent review, or release readiness.

## Validation and handoff

Run the exact focused tests in `PL-0421_VALIDATION_CRITERIA_V01.md`, plus `git diff --check`. Record all results, open model/license gates, and cleanup facts in `PL-0421_CODEX_LOG_V01.md`. Continue the queue after local implementation evidence is recorded.
