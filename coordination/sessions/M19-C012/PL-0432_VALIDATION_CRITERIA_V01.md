# PL-0432 Validation Criteria V01 — POVU SKU Shelf-Lineup Visualization

1. At least two and no more than twelve distinct immutable SKU revisions are required; each resolves to exactly the supplied Packaging Asset revision.
2. Height and body diameter must be present, positive, finite, supported (`mm` or `cm`), and have non-UNKNOWN per-field provenance. cm values convert deterministically to mm; source values are unchanged.
3. Output order is deterministic, non-overlapping with bounded gaps, and stores the exact SKU/asset revision IDs, normalized dimensions, and provenance classifications.
4. Qt presentation visibly labels the lineup as schematic/not product geometry or shelf-fit certification and shows the exact revision IDs, dimensions, and provenance.
5. Unknown, unsupported, stale, duplicate, mismatched, too-small, too-large, and malformed inputs fail closed. Inputs remain unchanged.
6. Focused synthetic tests, focused Ruff, and `git diff --check` pass using the existing local environment.
7. No Actions, paid CI, PR, `main` source push, native build, Installer build, owner data access, or release claim occurs.
