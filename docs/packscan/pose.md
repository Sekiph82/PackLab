# PackScan ARKit pose

PackScan uses a right-handed world/camera convention: `X` right, `Y` up, and
`Z` forward into the scene. Matrices are row-major 4x4 homogeneous transforms;
quaternions are explicitly `xyzw`. The image projection has `u` right and `v`
down, so the camera-to-image adapter applies the documented image-axis flip
without changing the stored 3D convention.

ARKit's native `simd_float4x4` is column-major and is copied by explicit
element order into the PackScan representation. The capture service records
the source frame and conversion provenance; it does not silently treat an
identity transform as a valid pose. `available`, `degraded`, and `unavailable`
are separate states, with confidence null for unavailable data. This contract
does not require LiDAR: ARKit tracking metadata can be recorded independently
of depth or scene reconstruction.
