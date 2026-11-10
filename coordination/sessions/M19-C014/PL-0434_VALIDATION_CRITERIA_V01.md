# PL-0434 Validation Criteria V01 — Packaging Technical Dossier Export

1. Reject missing, invalid or non-`PackagingAsset` source input before rendering.
2. Preserve exact `asset_id`, content-derived revision ID, canonical source digest, all source fields, original measurement units and recorded provenance; do not read source-link paths or bytes.
3. Return a valid single-page PDF entirely in memory, and verify it parses and renders through the already-installed Qt PDF APIs. No file is written by the export function.
4. The visible dossier states that it is packaging metadata only and makes no physical-accuracy, certification, compliance or manufacturing-authorization claim.
5. Manifest includes stable contract, source/PDF digests and explicit false authority flags; field ordering is deterministic.
6. Focused synthetic tests, targeted Ruff and `git diff --check` pass locally.
7. Zero Actions/paid CI, no PR, no source push to `main`, no native/Installer build, no live/private data and no release claim.
