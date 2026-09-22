# PackLab marker detection

`packlab_core.calibration.marker_detection.detect_markers` is the PackLab-owned
boundary around OpenCV ArUco/AprilTag detection. It loads only the pinned
`DICT_APRILTAG_36h11` dictionary from the marker policy, accepts non-empty
uint8 grayscale or 1/3-channel images, and returns marker IDs, four ordered
corners, geometry-quality metadata, and detector/dictionary provenance.

Corners are deterministic image pixels in `x` right / `y` down coordinates,
rotated to a top-left start and normalized to clockwise order. The fixed
`cornerSubPix` window, iteration count, and epsilon are part of the result
provenance. The quality score describes image-space marker geometry; it is not
a detection probability and is not a physical accuracy score.

Malformed/unsupported images, duplicate IDs, OpenCV detection failures, and
missing OpenCV are returned as bounded status/error results rather than
crashing unrelated workflows. A no-marker image is a normal `no_markers`
result. This detection API intentionally has no millimetre, scale, distance,
printer, camera, or pose inference. Scale estimation is a later calibration
stage.

Positive tests generate tiny synthetic markers with OpenCV in a temporary
workspace. Tests that run without OpenCV still cover pinned constants and
unsupported-input boundaries; no private or device image is required.
