# CLAUDE_PEER_REVIEW - PL-0492 oval follow-ups (PR #44, head 6759d02c)

Independent reviewer, not implementer.

Tests (local): oval core+studio 19 passed; overlay, scene package, CAD label analysis, metric binding, top disc, labels export/per-part, package families 84 passed, 1 skipped. Real Blender jar smoke passed in 26 s (idle machine).

Owner Scan Master 54ea0103: OVAL 61.7 x 33.6 x 166.8, neck 21.4, tilt 0.65 deg. A 10 deg tilt gives the same numbers. The fit takes 10.1 s: two passes, since 0.65 > 0.5 deg.

Probes: an 8 mm offset neck and 4 % / 15 % tapers are not levelled (tilt 0). Wrap, seam (+Y, as cylinder), arc direction, mitres and dieline mm are correct.

HIGH: none.

MEDIUM
- oval_section_fit.py `_axis_drift`: a body that leans by design (sheared, 2.9 deg) is "levelled". Its height changes 160 -> 162.1. The base-plane normal is not checked.

LOW
- labels_view.py:400-403: if Add is pressed without Suggest, it uses spinbox u 0..1 (the whole side half).
- `_suggest_prism_zone` builds a probe binding, so the BREP is sampled twice (the ~10 s).
- The real Blender prism overlay has not been rendered.

Blender timeout: comes from the environment or load, not this PR.

Verdict: PASS.
