# CLAUDE_PEER_REVIEW - PL-0484 closure placement (PR #32, head 93057d62) V01

Reviewer: independent Claude peer (not implementer). Evidence: diff origin/main...93057d62; 19 focused tests pass (core + studio, offscreen); own synthetic probes, seeds 21/22.

## HIGH
- H1 `core/src/packlab_core/part_placement.py:372-381`: blind band [cut-gap, cut+gap/2]. A same-diameter lid 3 mm too short (12 vs 15 mm) is PLACED with clean metrics (NEAR_CLEARANCE), lid 3 mm high, engaged 10 vs 13 mm (both seeds). The assembled skirt-bottom step is never checked. Fix: check that step against `cut`.

## MEDIUM
- M1 `:396-413`: gross interference still returns PLACED (CANDIDATE_OVERLAP): upside-down lid 0.42-0.45, neck 2.5 mm taller 0.35. Refuse above a bound.
- M2 `:410`: `overlap_depth_estimate` (mm in core `assembly_clearance.py:489`) is set to a point-share fraction.

## LOW
- L1 `project_parts.py:107-112`: stale check compares input paths only, not `cloud_sha256`/scale.
- L2 Placed-cloud sha256 missing from record/graph. Colours dropped.
- L3 A 4 deg cocked lid is refused (free_space_conflict). Conservative, but not documented.

OK: wrong diameter/body, floaters, tab-lid yaw (0.5 mm), sparse refusals, cancel, worker thread, METRIC_UNVERIFIED, mold_use_authorized=False.

Verdict: CHANGES_REQUIRED (H1, M1, M2).
