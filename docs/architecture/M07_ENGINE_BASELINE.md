# M07 reconstruction engine baseline

This record is implementation evidence, not distribution approval or legal advice.

## PL-0158 — COLMAP

| Field | Selected baseline |
| --- | --- |
| Engine | COLMAP |
| Version | `3.12.6` |
| Source | https://github.com/colmap/colmap |
| Release tag | https://github.com/colmap/colmap/tree/3.12.6 |
| Source revision | `4d5b60e19ad268072adaf1267d21fa38a9a828ca` |
| Windows source/build route | Official release Windows binaries or reproducible source build through vcpkg; PackLab does not bundle or download it |
| License evidence | https://colmap.github.io/license.html |
| License record | New BSD / 3-clause BSD for COLMAP itself; third-party dependencies and resulting binary obligations require separate review |
| Binary SHA-256 | Not available because no COLMAP executable is installed on the builder host |
| PackLab integration | External executable discovered through explicit configuration or safe PATH lookup |
| Validation boundary | Exact source identity is recorded and deterministic parser fixtures validate the expected version string; this is not a claim of native engine execution on this host |

The selected record makes no unsupported redistribution or license-clearance claim. The baseline is a reproducible source/build identity for later owner-controlled installation and packaging review.

## PL-0159 — OpenMVS

| Field | Selected baseline |
| --- | --- |
| Engine | OpenMVS |
| Version | `2.4.0` |
| Source | https://github.com/cdcseacave/openMVS |
| Release | https://github.com/cdcseacave/openMVS/releases/tag/v2.4.0 |
| Source revision | `58117204c86bbb11a0b25b26a8987676cf11274d` |
| Windows source/build route | Official release Windows x64 assets or reproducible source build; PackLab does not bundle or auto-download it |
| License evidence | https://github.com/cdcseacave/openMVS/blob/v2.4.0/LICENSE |
| License record | GNU AGPL-3.0; **HIGH LICENSE ATTENTION** |
| Binary SHA-256 | Not available because no OpenMVS executable is installed on the builder host |
| PackLab integration | External executable discovered through explicit configuration or safe PATH lookup |
| Validation boundary | Exact source identity is recorded and deterministic parser fixtures validate the expected version string; this is not a distribution-clearance claim |

OpenMVS remains subject to explicit review before bundling, modification, linking, installer distribution or network/service deployment. The record does not conclude that a future PackLab distribution is compliant or non-compliant.
