# PL-0396 — Low-cost packaging scan-station starter BOM

## Purpose and design envelope

This is a procurement-neutral starter definition for future PackLab packaging capture. It is a planning artifact, not a tested station or a purchase authorization. The initial single-operator tabletop design envelope is: package footprint diagonal no greater than 250 mm, package height no greater than 400 mm, and gross package-plus-fixture load no greater than 5 kg. The turntable target is at least 350 mm usable diameter with a documented working-load rating of at least 10 kg. The table target is 600 × 600 mm. Larger or heavier products require a larger rated support, suitable background and camera-clearance review. A 5 L jerrycan is only a planning category; actual packages must be measured against the envelope before this station is considered suitable.

Kenya vendor availability, local pricing, mains plug compatibility, import duty and delivery are not verified. No brand/model purchase is recommended. Functional requirements are listed so the owner can source equivalent local equipment later.

## Minimum BOM

| Qty | Component | Minimum requirement | Use / boundary |
| --- | --- | --- | --- |
| 1 | Manual turntable or lazy-Susan platform | At least 350 mm usable diameter, stated working load ≥10 kg, low wobble, non-slip/removable top, visible 15° index marks or a removable index ring | Supports controlled angular presentation. The load figure is a design target for the support, not a measured capacity claim for any product. |
| 1 | Rigid capture tabletop | Flat, stable surface at least 600 × 600 mm; does not rock under the turntable and object | Supports the turntable only. Camera tripod and light stands are independently placed on a stable floor around the table and positioned from floor marks measured relative to the table/turntable origin. |
| 1 | Matte background sweep / board set | Non-gloss white and mid/dark neutral sheets, large enough to fill the camera background for the product envelope | Choose a contrasting background for the actual object; keep it stationary and avoid glossy printed patterns. |
| 1 | Phone camera support | Stable tripod with adjustable height/tilt and a locking phone clamp; load rating ≥2 kg; remote shutter or timer | Prevents handheld shake. Tripod may be repositioned around a stationary object to obtain different viewpoints. |
| 2 | Diffused LED panels | Matching pair, daylight setting near 5,000–5,600 K, CRI ≥95 where stated, flicker-free claim, diffusers, independently dimmable or positionable | Use matching settings and fixed positions within a capture set. CRI/flicker specifications must be verified from each product datasheet. |
| 2 | Boom-arm light stands with counterweight, and diffusers | Stand plus boom able to hold the selected panel with its center 1300 mm above the tabletop and about 1.0 m horizontally from the stand foot (foot at 1300 mm radius and ±105°, panel at 300 mm radius and ±90° from the turntable axis), with the manufacturer's rated load and a counterweight/sandbag; diffusion material rated for continuous-light use and kept clear of hot fixtures | Holds the two panels overhead per PL-0397 revision 02 so they stay out of the camera frame during a full camera orbit. Floor-level panels on the camera orbit failed the PL-0397 geometric dry-run. Verify boom stability before placing it over a package. |
| 1 | Matte calibration board | A4 ChArUco or checkerboard with known printed square/marker dimensions, rigid flat backing, non-gloss surface | Used to calibrate the camera at multiple orientations. Measure a printed board before relying on the nominal print scale. OpenCV documents a 7×5 ChArUco board with 30 mm squares and 15 mm markers as a printable example. |
| 1 | Known-length scale reference | Steel scale bar or ruler with a specified length and readable graduations | Provides an image scale reference. Call it metrologically traceable only when current calibration/verification evidence establishes traceability to a stated reference standard; a printed or unverified ruler does not establish traceability or camera accuracy. |
| 1 | Basic measurement tool | 150 mm caliper with stated accuracy/resolution; use for accessible local features only | Reference measurements for small dimensions. Resolution is not accuracy; retain tool identity and calibration/verification evidence. |
| 1 set | Reusable station marks and capture notes | Removable center/orientation marks, tape measure, and a record sheet for camera, lens/zoom, distance, heights, light positions, and turntable angle | Makes the setup repeatable on paper; physical repeatability still needs PL-0401 trials. |

## Low-cost choices and optional upgrades

The baseline uses a manual indexed platform, ordinary locking tripod/phone clamp, two matched diffused LED panels, and printed calibration/reference targets. Do not buy a motorized platform for the initial software-validation station. As a current market comparison, a motorized Proaim product page lists a 20 kg payload turntable at US$1,782; it is an optional automation example, not a low-cost baseline or Kenya quote. Equivalent locally available rated manual platforms may differ in cost and quality and have not been inspected.

An optional remote shutter can reduce touch-induced movement. A powered/indexed turntable may be assessed only after station trials show that manual indexing is the limiting factor and the resulting image motion is compatible with the selected reconstruction lane.

## Camera and turntable capture caution

COLMAP's official tutorial describes SfM input as overlapping views from different viewpoints and advises moving between viewpoints rather than taking images from one location while only rotating the camera. A fixed camera with a rotating object/turntable is a distinct capture configuration: moving background/turntable features can disagree with object motion. Agisoft's turntable workflow recommends an empty-platform image, roughly 10–15° turns when the camera is fixed, and background masking. That is evidence for a different software workflow, not proof of COLMAP compatibility.

For PackLab's pinned COLMAP lane, keep the object in one orientation and stationary on the turntable for a standard image set, and reposition the camera around it. Do not rotate the object between image subsets and merge those images into an ordinary COLMAP set unless object-motion/background handling has been independently validated for that exact workflow. If a turntable-aware alternate capture is later used, keep it as a separate mode with explicit metadata and its own validation; do not infer compatibility from the Agisoft procedure.

## Evidence and acceptance limits

- OpenCV's calibration-pattern documentation gives a printable ChArUco example with a defined square/marker size and notes the board geometry/dictionary requirements. This is a printable software target, not a certified metrology artifact.
- A current Kaiser LED panel datasheet lists CRI 95, 5,600 K and flicker-free operation as example specifications. This supports the chosen feature requirements; it does not establish the output of an arbitrary panel or the illumination level of the complete station.
- On 2026-11-04, the Proaim product listing reported 20 kg payload and US$1,782, while its storefront marked the item sold out. This is a dated high-cost price/specification comparison only; it is not a recommendation or available purchase, and global pricing does not establish Kenya availability or cost.
- COLMAP and Agisoft capture guidance are cited above for viewpoint and turntable workflow limits.
- No station was assembled or measured. No real camera calibration, dimensional accuracy, scan repeatability, Kenya sample capture, supplier procurement, or physical acceptance is claimed.

## References

- COLMAP, [Tutorial: image capture and viewpoints](https://colmap.github.io/tutorial.html).
- OpenCV, [Camera calibration pattern documentation](https://github.com/opencv/opencv/blob/5.x/doc/tutorials/calib3d/camera_calibration_pattern/camera_calibration_pattern.markdown).
- Kaiser Fototechnik, [LED Desktop Light 5850 specifications](https://www.kaiser-fototechnik.de/en/produkte/artikel.php?nr=5850).
- Proaim, [360° rotating product-photography platform specifications and price](https://www.proaim.com/collections/new/products/proaim-turntable-360-rotating-platform-with-joystick-controller-for-product-photography-video).
- Agisoft, [Turntable capture scenario and processing workflow](https://agisoft.freshdesk.com/support/solutions/articles/31000163268-turntable-capturing-scenario-and-processing-workflow).
