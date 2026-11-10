# PL-0397 — Repeatable lighting and camera layout

## Status and scope

This is a proposed starting recipe for the PL-0396 tabletop envelope. It is not physically trialled. The distances and angles below are engineering starting values for later PL-0401 repeatability measurements; they are not sourced performance guarantees. Actual 5 L/large-package samples must fit the PL-0396 boundary (250 mm footprint diagonal, 400 mm height, 5 kg gross package-plus-fixture load) before using this layout.

## Station coordinate system

- Put the origin at the turntable rotation center on the tabletop: `x` left/right, `y` toward the camera, `z` upward from the tabletop. Project the origin vertically to the surrounding floor for camera/stand-foot coordinates.
- The 600 × 600 mm tabletop supports the turntable and object only. Put the phone tripod and light stands on a separate stable floor around the table; do not put their feet on the tabletop. Mark the projected origin, camera orbit, both light-stand feet, turntable zero-orientation mark, and each stand height. Measure each floor position horizontally from the projected turntable center, not from a table edge.
- Keep stand feet and power leads outside the operator's camera orbit; route and secure cables along the station perimeter so the capture path stays clear. Follow the selected fixture's own stability and operating instructions.
- Keep the turntable and object orientation fixed throughout one standard COLMAP capture set. Move the camera between viewpoints; record any changed object orientation as a separate capture mode and do not merge it into the ordinary set until validated.

## Proposed baseline layout

| Component | Starting coordinate/setting | Setup check |
| --- | --- | --- |
| Phone lens to turntable axis | 800 mm horizontal distance | Measure from the active camera lens to the axis. Frame the full package with margin; if the sample does not fit, change distance and record it. Do not change digital zoom or switch lenses within a set. |
| Camera heights | Three lens-center heights: 120 mm, 200 mm, and 320 mm above the tabletop | These correspond to low/mid/high viewpoints for the 400 mm planning envelope. Aim each view at the package center of height; check shoulders, base and top remain visible. |
| Camera orbit | 12 marked azimuth positions at 30° increments, with overlapping views | Treat as a starting coverage pattern only. Check image overlap and focus; add views where surfaces are occluded. COLMAP guidance favors different viewpoints and notes more images are not automatically better. |
| Left and right diffused panels (revision 02) | Overhead on counterweighted boom arms: panel centers 300 mm from the turntable axis at azimuth −90°/+90° (left/right of the initial front axis), 1300 mm above the tabletop, emitting face down/inward toward the package; stand feet on the floor at 1100 mm horizontal radius, azimuth −90°/+90° | Keep both panel models, color-temperature setting, diffusion, orientation and stand marks constant. Confirm highlights do not wash out label/contour features. Never place a panel on the camera orbit or below the 1300 mm height without rerunning the dry-run check. |
| Background | Matte white, black or neutral board selected for object contrast | Keep background fixed for the whole set. Avoid moving high-contrast texture/features behind the object. |
| Camera mode | Same phone, active lens, resolution, orientation and focus/exposure/white-balance behavior throughout the set; lock these where the capture software permits | Record any setting that cannot be locked. Do not mix lens, resolution or digital zoom variants in one reconstruction set. |

### Geometric dry-run (revision 02, 2026-11-10)

`core/src/packlab_core/scan_station_layout.py` checks a layout with pinhole geometry for the iPhone 16 main camera (26 mm-equivalent, 4:3; ≈67.3° × 53.1° FOV, both orientations): the PL-0396 envelope must fill ≤0.9 of the half-FOV from every planned viewpoint, no light-emitting surface may fall inside the frame, and each light-stand foot must be ≥300 mm from every camera station. `tests/core/test_scan_station_layout.py` runs it.

- Revision 01 (panels on the floor at 800 mm radius, ±45°, 650 mm high) **failed**: with a full 360° camera orbit, the opposite-side panel is inside the frame for most rear viewpoints (looking straight into the light), and both stand feet sit on the camera orbit only 209 mm from the 30°/60°/300°/330° camera stations.
- Revision 02 (overhead panels above) passes in portrait and landscape, and still passes with 500 mm panels.
- This is geometry only. It does not model flare from outside the frame, bounce light, shadows, lens distortion or real phone optics, and it is not a physical trial; PL-0401 still owns physical repeatability. Rerun the check for any changed distance, height, panel or stand position.

The 800 mm and 120/200/320 mm camera values and the revision-02 light positions are reproducibility targets, not a result from a physical station. They may be changed to fit a real sample or field of view, but the operator must record the actual positions. Keep camera-to-object distance fixed across each height/orbit pass unless framing requires an explicitly logged adjustment. The distance coordinates describe supports on the floor, so the 600 × 600 mm tabletop does not need to contain the tripod/light-stand footprints.

## Capture procedure for later physical validation

1. Place the empty object-free station reference board and calibration target in the documented position; capture camera-calibration images at varied board orientations as required by the calibration procedure. Record the measured printed dimensions.
2. Remove the board from the object area, place the package centered on the fixed turntable, and note package ID/status and orientation mark. Do not use an actual Kenya production identifier until the real factory library process assigns one.
3. Set both matched diffused lights to the same fixed daylight setting and output. Record model, setting, stand coordinates, panel center height, panel-to-axis distance and any diffuser.
4. Capture the camera orbit at the three defined heights, moving the camera around the stationary package. Keep the object and surrounding background stationary. Pause after repositioning to avoid motion blur.
5. Review coverage, focus, blur, glare, clipped highlights, background feature contamination and label/edge visibility before accepting the set. A failure triggers a documented recapture, not silent mixing with changed settings.
6. Save the setup record with the capture. Any changed camera/light layout starts a new recorded set. Do not claim the set is metrically accurate until calibration and physical reference validation have separately passed.

## Required setup record

Record: station/BOM revision; date/operator; package envelope and object orientation; tabletop height above floor; phone/camera model and active lens; resolution; focus/exposure/white-balance behavior; camera lens-to-axis distance; each camera height and azimuth; turntable index/orientation; both light model IDs/settings/coordinates/diffusers; background material/color; calibration-target ID and measured dimensions; scale-reference ID and verification record; exceptions; coverage/glare/focus review; and whether the images are a standard COLMAP set or separately validated turntable-aware mode.

## Evidence and limits

COLMAP describes SfM as matching overlapping views from different viewpoints and warns that changing only camera rotation at one position is insufficient. Agisoft's turntable guidance says lighting should remain stable and diffuse lighting is useful; its fixed-camera turntable workflow uses empty-platform images, approximately 10–15° object turns and background masks. These are supporting workflow references, not a substitute for validating PackLab's pinned COLMAP lane.

References:

- [COLMAP Tutorial — capture viewpoints](https://colmap.github.io/tutorial.html)
- [Agisoft — turntable capture scenario and processing workflow](https://agisoft.freshdesk.com/support/solutions/articles/31000163268-turntable-capturing-scenario-and-processing-workflow)
- [OpenCV — calibration patterns](https://github.com/opencv/opencv/blob/5.x/doc/tutorials/calib3d/camera_calibration_pattern/camera_calibration_pattern.markdown)

No physical station was assembled. No actual Kenya package was measured or captured. No lighting repeatability, camera calibration, dimensional accuracy or production acceptance is claimed; those are future physical/measurement tasks.
