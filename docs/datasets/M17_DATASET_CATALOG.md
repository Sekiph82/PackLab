# M17 Packaging Dataset Catalog

## Purpose and local storage

M17 builds reproducible software validation inputs for PackLab's reconstruction, segmentation, calibration, measurement, Scan Master and Design Model boundaries. Full datasets, real source archives and generated render sets live outside Git at `%LOCALAPPDATA%/PackLab/datasets/M17`. The generator, validators, compact metadata, source/license catalog and test code may live in Git. Do not copy source images/models into Git unless a separately reviewed small fixture is demonstrably safe to redistribute.

No Kenya factory or field scans currently exist. Synthetic geometry, virtual-camera calibration, expected dimensions and tolerances are simulated validation truth only; they are not physical observations or Kenya acceptance.

## Source register

### YCB Object and Model Set

- Official index: <https://ycb-benchmarks.s3.amazonaws.com/index.html>
- The official project states that Berkeley scan-rig data includes textured meshes, point clouds, 600 high-resolution RGB and RGB-D images per object, and that Google-scanner assets include 16k/64k/512k polygon models with textures. The dataset license is CC BY 4.0; the project's downloader code is MIT. Some transparent objects may have incomplete meshes.
- Initial intended real references: `006_mustard_bottle` and `021_bleach_cleanser` as real packaged consumer containers; selected photographs are real captures and the supplied meshes are scanned model references. Their labels/product appearance remain third-party source content. CC BY attribution does not grant trademark/product-trade-dress rights; no such product identity is presented as cleared or redistributed by PackLab.
- Keep full archives and any derivative extracts in the private local dataset root. Record each exact archive byte count and SHA-256 after download; keep image and mesh provenance separate.
- The official YCB index states the dataset license and links the exact per-object archives. Preserve the official source URL plus downloaded archive byte count/SHA-256. If an archive identity or content does not match the linked asset/expected layout, quarantine it and use the synthetic fixture for that scenario; an archive need not repeat the license text.

### Google Objectron — candidate only, not yet imported

- Official dataset description: <https://github.com/google-research-datasets/Objectron/blob/master/README.md>
- License: Computational Use of Data Agreement 1.0, not a blanket open-content license. It restricts use to computational use and binds redistribution to passing on agreement/attributions. Objectron may be considered for private local analysis only after downloading a specific bounded object clip and preserving the agreement; never include its data in a public fixture without satisfying those terms.
- License text: <https://github.com/microsoft/Computational-Use-of-Data-Agreement>

### Amazon Berkeley Objects — candidate only, not yet imported

- Official dataset: <https://amazon-berkeley-objects.s3.amazonaws.com/index.html>
- Official current index identifies CC BY 4.0 and includes catalog imagery, spin sequences, glTF models, camera, mask, normals, depth, and material render data. Its page lists archive sizes; do not download the multi-gigabyte full imagery/spin/model archives for this bounded M17 benchmark.
- Older papers/blogs describe the earlier CC BY-NC release. The current official index says CC BY 4.0, but an exact item/archive must retain its own current README/license copy and SHA-256 before use. Do not assume an old mirror or paper was relicensed. Third-party rights beyond copyright may remain.

## Controlled synthetic supplement

The deterministic Blender generator produces parameterized bottle, jerrycan, jar, closure, trigger, pump, tube and sachet fixtures in the local `synthetic/` dataset. It labels polymer appearance, translucency, roughness, nominal sizes, tolerances, camera intrinsics/extrinsics, light and render settings as simulation assumptions. Version 2 corrects generated assembly extents against serialized mesh ground truth, removes the visible studio-floor horizon, and improves transparent-material contrast. It is intended for software boundary/regression coverage and cannot validate real material optics or physical accuracy by itself.

## Rights and terms

The PackLab-created dataset notice is restricted to owner-controlled internal PackLab development/CI and the owner's design office/future factory. It does not grant external reuse, sublicensing, redistribution, sale or marketing. Upstream licenses and attribution govern included third-party data. This scope does not change root repository/dependency licenses and has not received formal legal review.

