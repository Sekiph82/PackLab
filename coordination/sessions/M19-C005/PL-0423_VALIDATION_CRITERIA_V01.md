# PL-0423 Validation Criteria V01 — Bounded Fit-Parameter Optimization Proposal

1. Request binds to exact Design Model and Scan Master revisions plus geometry/deviation evidence digests.
2. Measured-dimension constraints have positive finite targets and tolerances and safe parameter IDs.
3. Candidate parameter values are finite, unique, deterministic and within each explicit target ± tolerance; candidate deviation is finite, nonnegative and no greater than the declared budget.
4. Suggestion serialization is non-authoritative and excludes raw geometry, scan content, paths, supplier and owner data.
5. Explicit acceptance rejects stale model/source ancestry, missing/nonnumeric parameter, out-of-bound candidate, deviation-budget violation, and unproposed candidate.
6. Acceptance produces an immutable successor through `revise_design_model_revision`, with same Scan Master binding and deferred physical-accuracy/mold-use authority.
7. Backend deviation/evaluation values remain untrusted proposal estimates. The successor cannot be treated as geometrically validated without downstream regeneration and comparison evidence.
8. Fake backend only, no model package/checkpoint/runtime installed, downloaded or enabled.
9. Exact local validation: `python -m pytest -q tests/core/test_dimension_fit_proposal.py` with `PYTHONPATH=core/src`.
10. `git diff --check` passes; no Actions, paid CI, PR, main source push, native build, or release claim.
