from __future__ import annotations

from packlab_core.engine_baseline import COLMAP_BASELINE, baseline_records


def test_colmap_baseline_is_exact_and_reproducible() -> None:
    assert COLMAP_BASELINE.engine_id == "colmap"
    assert COLMAP_BASELINE.version == "3.12.6"
    assert COLMAP_BASELINE.source_ref == "3.12.6"
    assert COLMAP_BASELINE.source_revision == "4d5b60e19ad268072adaf1267d21fa38a9a828ca"
    assert COLMAP_BASELINE.binary_sha256 is None
    assert "third-party" in COLMAP_BASELINE.license_name
    assert baseline_records() == (COLMAP_BASELINE,)
