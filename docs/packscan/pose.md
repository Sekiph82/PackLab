# PackScan ARKit pose

PackScan stores a right-handed pose convention with `+X` right, `+Y` up, and
`+Z` out of the camera/device screen side; therefore the camera viewing
direction is `-Z`. Matrices are row-major 4x4 homogeneous transforms in JSON,
multiplied as column vectors on the right (`p' = M * p`), and all stored
translation components use metres. Quaternions are explicitly `xyzw`. The
image projection has `u` right and `v` down, so the camera-to-image adapter
applies the documented image-axis flip without changing the stored 3D
convention.

ARKit's source frame is the same right-handed basis: `+X` right, `+Y` up,
`+Z` out of the device screen side, and camera viewing direction `-Z`. The
frozen ARKit-to-PackScan mathematical conversion is therefore the identity:
`T_P = T_A` and `q_P = q_A`. Apple's `simd_float4x4` column-oriented storage
access and PackScan's row-major nested JSON arrays are serialization/layout
handling only; they do not introduce a transpose or geometric reflection.
The quaternion component mapping preserves `xyzw` exactly: `(x_P, y_P, z_P,
w_P) = (x_A, y_A, z_A, w_A)`.

`available`, `degraded`, and `unavailable` are separate states: available pairs
with normal tracking, degraded with limited tracking, and unavailable only with
not-available tracking and null confidence; unavailable records contain no
transforms or quaternion. The versioned conversion and coordinate-convention
identifiers are required on stored records. This contract does not require
LiDAR: ARKit tracking metadata can be recorded independently of depth or scene
reconstruction. No Windows runtime claim is made for native ARKit.
