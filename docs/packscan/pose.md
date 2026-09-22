# PackScan ARKit pose

PackScan stores a right-handed world/camera convention with `X` right, `Y` up,
and `Z` forward into the scene. Matrices are row-major 4x4 homogeneous
transforms, multiplied as column vectors on the right (`p' = M * p`), and all
stored translation components use metres. Quaternions are explicitly `xyzw`.
The image projection has `u` right and `v` down, so the camera-to-image adapter
applies the documented image-axis flip without changing the stored 3D
convention.

ARKit's source frame is right-handed with `+X` right, `+Y` up, and the camera
viewing direction along `-Z`; PackScan's stored camera basis uses `+Z` forward.
The frozen basis conversion is the explicit reflection
`B = diag(1, 1, -1, 1)`, not a memory-layout transpose. For an ARKit
camera-to-world matrix `T_A`, the PackScan matrix is exactly
`T_P = B * T_A * B^-1` (and `B^-1 = B`), using the row-major/column-vector
convention above. This maps an ARKit camera forward vector `(0, 0, -1)` to the
PackScan forward vector `(0, 0, +1)` and negates the converted Z translation.
The matching quaternion conversion preserves `xyzw` order and is
`(x_P, y_P, z_P, w_P) = (-x_A, -y_A, z_A, w_A)`.

`available`, `degraded`, and `unavailable` are separate states: available pairs
with normal tracking, degraded with limited tracking, and unavailable with
not-available tracking and null confidence. The conversion identifier and
coordinate convention are required on stored records. This contract does not
require LiDAR: ARKit tracking metadata can be recorded independently of depth
or scene reconstruction. No Windows runtime claim is made for native ARKit.
