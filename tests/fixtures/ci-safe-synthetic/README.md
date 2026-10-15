# CI-safe synthetic media

This directory contains six deterministic, one-pixel or minimal ASCII
synthetic fixtures for CI policy and import-boundary tests: PNG, JPEG, STL,
PLY, STEP, and DXF. They contain no captured object, person, location, supplier,
customer, or Kenya production data.

`tools/ci/ci_safe_data_policy.json` pins each payload's exact byte length and
SHA-256 and caps every approved fixture at 64 KiB. New media fixtures require
provenance review and an explicit manifest entry. Renaming a media file or
placing it under a similarly named fixture folder does not grant an exemption.

The same policy separately pins the existing PackLab-owned calibration SVGs
and Studio ICO by path, byte length, and SHA-256 so those reviewed source
artworks remain available without opening an exemption for other artwork.
