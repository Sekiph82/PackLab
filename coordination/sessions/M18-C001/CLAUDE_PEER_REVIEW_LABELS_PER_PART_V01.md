# CLAUDE_PEER_REVIEW: PL-0487 labels per part (PR #33, head 03379e8c)

Separate reviewer. My runs: tests/studio 428 passed, 3 skipped; core label tests 148 passed, 2 skipped. CI passes.

## HIGH
- design_workbench.py:1116,1155 `label_preview_points` maps the artwork column straight to zone u. Blender `_viewer_orientation` mirrors u for front, back and wrap, because u runs to the viewer's left. As a result, side-wall labels in the Assembled preview show mirrored. Tests check colours only.

## MEDIUM
- labels_view.py:697-700 applies the PL-0484 scan-frame `closure_on_body` rotation and Z offset to the Measure-frame Design Models, and drops XY. The frames are not proven to match (yaw, flipped closure). The test uses an identity rotation only.
- restore_labels:661 sets the outer radius from the boundary ratio but the inner radius in absolute mm. Re-applying to a model with a different radius therefore changes the outer size in mm.

## LOW
- The PLANAR_DISC dieline JSON `boundary_vertices` stays a square. Only the SVG draws circles.
- No core-level tests cover TOP when the face points down, trims are not circles, or the disc is off-axis.
- show_assembled runs OCC and image rendering on the UI thread.

Correct: zone math, area, top orientation, dieline radii, staleness.

**Verdict: CHANGES_REQUIRED**
