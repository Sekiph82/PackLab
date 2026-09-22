# iPhone main-camera calibration procedure

PackLab M02 baseline is the iPhone 16 Standard back main wide camera at `1.0x`.
This procedure does not assume LiDAR, Pro-only lenses, depth sensors, or any
device capability outside that baseline.

No owner-produced iPhone calibration profile is included in this repository.
Until a physical owner session produces one, PackLab records the profile status
as `unavailable` and must not claim measured camera calibration.

## When recorded metadata is enough

Recorded EXIF and device API intrinsics may be used as capture metadata when
the PackScan only needs traceability or a best-effort reconstruction input.
They are sufficient only when all of these bindings are recorded together:

- device model: `iPhone 16 Standard`;
- lens identity: `main_wide_camera_1x`;
- camera position: back camera;
- image resolution in pixels: `image_width_px` and `image_height_px`;
- orientation and pixel coordinate convention;
- zoom factor: exactly `1.0x`;
- focus mode and, if available, focus distance in metres;
- capture app version and calibration policy version.

A dedicated calibration is required before PackLab treats intrinsics as a
measured profile, before using a profile across a different resolution, lens,
zoom factor, focus regime, capture app version, or device model, and before any
accuracy or benchmark claim. Missing EXIF, unavailable device intrinsics, an
unknown lens identity, digital zoom, or a resolution mismatch also require a
dedicated calibration or a fail-closed `unavailable` profile.

## Dedicated capture procedure

Use only a physically accepted PackLab printed calibration mat whose pre-use
verification record is `ACCEPTED_FOR_CAPTURE`. Capture with the back main wide
camera, select `1.0x`, disable lens switching, and avoid portrait/depth/LiDAR
modes. Lock focus or record the device-reported focus distance for each frame.
Do not use screenshots, cropped exports, or images rescaled outside the capture
pipeline.

The minimum view set is seven views:

- fronto-parallel near;
- fronto-parallel far;
- yaw left;
- yaw right;
- pitch up;
- pitch down;
- corner coverage with markers near image edges.

Every accepted frame must preserve original pixel dimensions and metadata. The
operator records rejected frames separately; missing views cannot be filled with
synthetic observations.

## Validation outputs

A produced calibration result records:

- `reprojection_rmse_px`, in image pixels;
- `accepted_view_count`;
- `confidence_status` from the PackLab calibration confidence gate;
- linked `camera-intrinsics.schema.json` payload;
- printed-mat verification record ID;
- owner physical measurement status;
- full profile binding: device model, lens identity, resolution, orientation,
  zoom factor, focus mode, capture app version, and profile version.

The profile binding is exact. PackLab must not silently reuse a profile for a
different device, lens, resolution, zoom factor, focus regime, or app version.

## Schema

The calibration result contract is
`schemas/packscan/iphone-main-camera-calibration.schema.json`.

`candidate` and `measured` records require owner-device capture evidence and an
owner-completed physical measurement record. `unavailable` records must not
contain capture-run or validation-output data.
