# PL-0433 Validation Criteria V01 — Alternative Packaging Supplier Comparison

1. Reject fewer than two assets, duplicate asset revisions, invalid source types, or records whose canonical revision identity is invalid.
2. Preserve input order, exact asset IDs/revision IDs, explicit supplier names/IDs, and immutable source records.
3. Include only existing asset fields. Missing fields remain explicitly unknown. Every displayed value is accompanied by its field provenance classification.
4. Do not rank, score, recommend, infer unrecorded facts, or claim supplier compliance, quality, price, availability, certification, or suitability.
5. The in-memory Qt presentation visibly labels the comparison descriptive/non-authoritative and renders all selected alternatives without truncation of provenance or source identity.
6. Focused synthetic tests, targeted Ruff, and `git diff --check` pass using the existing local environment.
7. Zero Actions/paid CI, no PR, no source push to `main`, no native build, no private supplier data, and no release claim.
