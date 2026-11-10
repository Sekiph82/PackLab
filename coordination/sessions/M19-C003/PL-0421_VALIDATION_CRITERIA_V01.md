# PL-0421 Validation Criteria V01 — Package-Family Suggestion Contract

1. Requests and suggestions bind to safe asset/revision identifiers and content digests; serialized records contain no paths or raw content.
2. Candidate families are valid, unique, deterministically ordered and have finite confidence in `[0, 1]`.
3. Suggestion records are visibly generated/non-authoritative and cannot change a PackagingAsset by construction.
4. Acceptance requires explicit actor confirmation for the exact asset revision and suggestion digest; stale or mismatched acceptance fails closed.
5. Accepted family changes create an immutable PackagingAsset successor with `USER_DECLARED` field provenance and a separate acceptance evidence record; original asset remains unchanged.
6. The backend is a PackLab-owned protocol only; tests use a deterministic fake. No model package/checkpoint/runtime is installed or activated.
7. Exact local validation: `python -m pytest -q tests/core/test_package_family_suggestion.py` with `PYTHONPATH=core/src`.
8. `git diff --check` passes.
9. No GitHub Actions/paid CI, PR, main source push, native build, or release claim occurs.
