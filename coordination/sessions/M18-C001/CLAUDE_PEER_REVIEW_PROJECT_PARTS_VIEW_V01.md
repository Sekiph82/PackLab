# CLAUDE_PEER_REVIEW - PR #31 project parts view (PL-0485) - V01

Head 9d10d967. Local run: tests/studio (no test_reconstruction_execution.py) + tests/core/test_multiscan_alignment.py: 454 passed, 3 skipped. CI: only the signing-material scan ran (pass). No Windows test job ran.

## HIGH
- measure_design.py:1176-1191, 1242-1249: the Poisson mesh is promoted as `COLMAP_OPENMVS` "external-build" geometry. `mesh_method` is never written into the lineage or the limitations. `analyze_mesh_holes` gets `coverage_gap_vertex_indices=()`, so surface invented by Poisson can show up as hole-free scanned surface. It must be labelled as derived and closed by reconstruction (Open3D Poisson), and the low-density/filled vertices must be listed as coverage gaps. No test checks this.

## MEDIUM
- project_parts.py:571-573 with 597-624: if Cancel is pressed after the worker's last check, `_finish` still saves the record. The job then goes from CANCELLING to SUCCEEDED, so "discarded on cancel" does not hold. The test only cancels during alignment.
- No Windows CI for the new code.

## LOW
- Cancel or a failed record after `write_cloud`/`write_mesh` leaves orphan files in derived/parts.
- UI thread: the first `_cached_sha` in `refresh`, `_part_mesh` hashing and loading several clouds into the viewer all run on it.
- When the selected part has no cloud (Assembled missing), the label says "Use selected part" but the latest build is loaded.

## Verdict
CHANGES_REQUIRED
