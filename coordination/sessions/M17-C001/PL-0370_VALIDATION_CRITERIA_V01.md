# PL-0370 — Validation Criteria V01

1. The source archives are the exact official YCB mustard-bottle model, bleach-cleanser model and mustard RGB archive; actual byte lengths and SHA-256 values are recorded and verified.
2. Safe extraction yields two source 3D model packages and exactly 30 original RGB JPEGs selected across source camera groups, with no archive traversal, symlink/junction redirection or source-byte mutation.
3. Every extracted item is bound to source archive/member, file size/hash, YCB attribution and CC BY 4.0 URL.
4. Metadata states the YCB photos and scanned meshes are separate acquisitions and are not a registered camera/image/3D benchmark pair; source camera calibration and physical ground truth are unknown/unverified where absent.
5. Local validator checks path containment, file identity/hash, source archive integrity, license, attribution, source kind and uncertainty boundaries; negative tests cover malformed metadata/path forms.
6. All full source files and derived real references remain outside Git; no private Kenya scans or physical acceptance claims are created.
7. Local software validation is distinct from future Kenya physical validation, which remains incomplete until real facility/equipment and measured objects exist.
8. Comprehensive tests and consolidated independent/security reviews remain at the M17 milestone-end checkpoint; no task-level full test run is required.

