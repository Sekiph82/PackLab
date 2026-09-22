# PackLab calibration marker policy 1.0

The machine-readable source of truth is
`schemas/packscan/calibration-marker-policy.json`. PackLab selects the
OpenCV AprilTag family `DICT_APRILTAG_36h11`, passed through
`cv.aruco.getPredefinedDictionary` (or the equivalent C++ API constant).
OpenCV's current 4.13.0 reference lists this predefined dictionary and the
lookup API. The OpenCV ArUco reference describes the family as 6x6 bits with
minimum Hamming distance 11 and 587 codes. These are dictionary properties,
not a measured camera, printer, or physical detection-accuracy claim.

PackLab calibration mats actively reserve IDs `0..63` inclusive. IDs are
unique within an observation set; repeated IDs in one set are a collision.
IDs `64..586` remain reserved for future PackLab calibration expansion and
must not be assigned to application markers. No marker outside the dictionary
range `0..586` is valid for this policy. A later mat revision must add an
explicit policy version and collision-reviewed assignment; detection code must
load the machine-readable policy rather than silently selecting another
dictionary.

The nominal minimum marker side guidance is 40 mm, stored in millimetres. It
is a print-layout/readability floor for future mat assets only. It is not a
claim that a printer, camera, lens, distance, or detector achieves any
accuracy. Physical print verification and benchmark evidence remain owner and
device controlled.

The selected `packscan_marker_family` and `opencv_dictionary` values are
directly representable by the public marker-observation schema's required
family and dictionary strings. Marker observations still require their own
known geometry/provenance and never infer physical scale from this policy.
