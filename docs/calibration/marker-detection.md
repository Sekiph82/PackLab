# PackLab marker detection

`packlab_core.calibration.marker_detection.detect_markers` is the PackLab-owned
boundary around OpenCV ArUco/AprilTag detection. It loads the selected OpenCV
dictionary name from `schemas/packscan/calibration-marker-policy.json` and
resolves that policy value through `cv2.aruco.getPredefinedDictionary`. If the
policy dictionary cannot be mapped to the local OpenCV ArUco module, detection
returns a bounded `unavailable` result with an explicit policy-dictionary
error rather than substituting a fallback family. The detector accepts non-empty
uint8 grayscale or 1/3-channel images and returns marker IDs, four ordered
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
workspace. Tests that run without OpenCV still cover policy-driven dictionary
resolution, unsupported-policy rejection, injected duplicate-ID handling, and
unsupported-input boundaries; no private or device image is required.
