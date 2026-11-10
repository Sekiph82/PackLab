# PL-0386 — Validation Criteria V01

1. At least three real package-family `.packscan` inputs are processed by pinned COLMAP and OpenMVS.
2. Each produces verified textured reconstruction outputs and a lineage-bound Scan Master.
3. Failures, source digests, engine versions and output identities are retained.
4. Synthetic PLY/render fixtures are not accepted as reconstruction evidence.
5. Missing inputs/engines leave task incomplete with exact blocker.
