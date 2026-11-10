# PL-0416 — Validation Criteria V01

1. An artwork-only change creates a new SKU revision on the identical Packaging Asset revision. The asset and its geometry are untouched, and no geometry is copied.
2. New artwork is a new immutable revision bound through the existing zone, mapping and assignment contract. Stale or mismatched references are rejected.
3. History keeps the old artwork and SKU revisions, and the current lookup moves to the new revision.
4. Scope boundaries are explicit: label size, wrap or geometry changes route to PL-0417, and licence/permission is required.
5. A synthetic dry-run is provided. No real artwork, print fidelity or Kenya evidence is claimed.
