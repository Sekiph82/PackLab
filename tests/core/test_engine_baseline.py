from __future__ import annotations

from packlab_core.engine_baseline import COLMAP_BASELINE, OPENMVS_BASELINE, baseline_records


def test_colmap_baseline_is_exact_and_reproducible() -> None:
    assert COLMAP_BASELINE.engine_id == "colmap"
    assert COLMAP_BASELINE.version == "3.12.6"
    assert COLMAP_BASELINE.source_ref == "3.12.6"
    assert COLMAP_BASELINE.source_revision == "4d5b60e19ad268072adaf1267d21fa38a9a828ca"
    assert COLMAP_BASELINE.binary_sha256 is None
    assert "third-party" in COLMAP_BASELINE.license_name
    assert baseline_records() == (COLMAP_BASELINE, OPENMVS_BASELINE)


def test_openmvs_baseline_preserves_high_attention_license_boundary() -> None:
    assert OPENMVS_BASELINE.engine_id == "openmvs"
    assert OPENMVS_BASELINE.version == "2.4.0"
    assert OPENMVS_BASELINE.source_ref == "v2.4.0"
    assert OPENMVS_BASELINE.source_revision == "58117204c86bbb11a0b25b26a8987676cf11274d"
    assert "AGPL-3.0" in OPENMVS_BASELINE.license_name
    assert "HIGH LICENSE ATTENTION" in OPENMVS_BASELINE.license_name
    assert OPENMVS_BASELINE.binary_sha256 is None
