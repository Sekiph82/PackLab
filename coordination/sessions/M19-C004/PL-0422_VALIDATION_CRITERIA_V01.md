# PL-0422 Validation Criteria V01 — Parametric Section Placement Proposal Contract

1. Request binds to safe profile-fit/zone revision IDs and a digest of the exact zone record; no raw profile/scan content or paths serialize.
2. Candidate contains exactly three finite axial transitions, ordered within the fitted profile extent when accepted, plus finite confidence in `[0,1]`; candidate ordering is deterministic and IDs unique.
3. Suggestion is visibly generated/non-authoritative and cannot mutate source fit or zones.
4. Acceptance requires an explicit actor, reason and UTC timestamp, exact current fit/zone revision IDs, and a candidate contained in the suggestion.
5. Acceptance calls PackLab's existing `override_design_profile_zones` authority path. It returns a new immutable `MANUAL_OVERRIDE` with `review_required=True`; old zones and fit remain unchanged. It cannot promote physical accuracy or mold-use authority.
6. Fake backend only; no model runtime/package/checkpoint is installed, downloaded or activated.
7. Exact local validation: `python -m pytest -q tests/core/test_profile_zone_proposal.py` with `PYTHONPATH=core/src`.
8. `git diff --check` passes.
9. No GitHub Actions/paid CI, PR, main source push, native build, or release claim occurs.
