from __future__ import annotations

import hashlib
import json
import struct
import zlib

import pytest
from tests.core.test_label_zone_placement import _zone

from packlab_core.label_artwork import (
    LabelArtworkError,
    ingest_label_artwork,
    map_label_artwork_to_zone,
)
from packlab_core.label_zone import LabelZoneKind
from packlab_core.label_zone_placement import create_label_zone_placement_revision


def _svg(color: str = "red") -> bytes:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" '
        f'viewBox="0 0 200 100"><rect width="200" height="100" fill="{color}"/></svg>'
    ).encode()


def _chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def _png() -> bytes:
    header = struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0)
    pixels = b"\x00" + bytes((255, 0, 0, 255, 0, 255, 0, 255))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(pixels))
        + _chunk(b"IEND", b"")
    )


def _placement():
    _, _, zone = _zone(LabelZoneKind.FRONT)
    return create_label_zone_placement_revision(
        zone,
        zone.boundary,
        actor_id="operator-1",
        reason="Map artwork in normalized Label Zone coordinates.",
        created_at_utc="2026-10-04T14:00:00Z",
    )


@pytest.mark.parametrize(
    ("content", "media_type", "dimensions"),
    [(_svg(), "image/svg+xml", (200.0, 100.0)), (_png(), "image/png", (2.0, 1.0))],
)
def test_svg_and_png_assets_are_digest_bound(content, media_type: str, dimensions) -> None:
    asset = ingest_label_artwork(content)

    assert asset.content_sha256 == hashlib.sha256(content).hexdigest()
    assert asset.media_type == media_type
    assert (asset.width, asset.height) == dimensions
    assert asset.byte_size == len(content)
    assert asset.as_dict()["authority_class"] == "PRESENTATION_ARTWORK_ASSET"
    assert asset.as_dict()["changes_design_model"] is False
    assert asset.as_dict()["changes_cad_brep"] is False
    assert json.dumps(asset.as_dict(), sort_keys=True, allow_nan=False)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"<svg>",
        b"<!DOCTYPE svg [<!ENTITY x SYSTEM 'file:///secret'>]><svg>&x;</svg>",
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="NaN 0 10 10"/>',
        b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><image href="https://example.com/a.png"/></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>alert(1)</script></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><style>@import "https://example.com/x.css"</style></svg>',
    ],
)
def test_malformed_or_remote_active_svg_rejects_without_fetch(content: bytes, monkeypatch) -> None:
    import socket

    def no_network(*args, **kwargs):
        raise AssertionError("network fetch attempted")

    monkeypatch.setattr(socket, "create_connection", no_network)
    with pytest.raises(LabelArtworkError):
        ingest_label_artwork(content)


def test_png_crc_chunk_structure_and_decoded_size_are_validated() -> None:
    valid = _png()
    corrupted = bytearray(valid)
    corrupted[-5] ^= 1
    oversized_header = struct.pack(">IIBBBBB", 16_385, 1, 8, 6, 0, 0, 0)
    too_large = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", oversized_header)
    duplicate_header = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0))
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0))
    )

    with pytest.raises(LabelArtworkError, match="crc_invalid"):
        ingest_label_artwork(bytes(corrupted))
    with pytest.raises(LabelArtworkError, match="format_unsupported"):
        ingest_label_artwork(too_large)
    with pytest.raises(LabelArtworkError, match="ihdr_duplicate"):
        ingest_label_artwork(duplicate_header)


def test_oversized_content_and_private_local_path_are_bounded_and_not_persisted(tmp_path) -> None:
    source = tmp_path / "private_supplier_artwork.svg"
    source.write_bytes(_svg())
    asset = ingest_label_artwork(source)
    metadata = json.dumps(asset.as_dict(), sort_keys=True)

    assert str(source) not in metadata
    assert source.name not in metadata
    assert ingest_label_artwork(_svg()) == asset
    with pytest.raises(LabelArtworkError, match="size_out_of_bounds"):
        ingest_label_artwork(b"x" * (8 * 1024 * 1024 + 1))
    with pytest.raises(LabelArtworkError) as error:
        ingest_label_artwork(tmp_path / "private_missing_file.svg")
    assert str(tmp_path) not in str(error.value)


@pytest.mark.parametrize("fit_mode", ["CONTAIN", "COVER", "STRETCH"])
def test_artwork_mapping_has_deterministic_fit_crop_and_normalized_transform(fit_mode: str) -> None:
    placement = _placement()
    artwork = ingest_label_artwork(_svg())

    first = map_label_artwork_to_zone(artwork, placement, fit_mode=fit_mode)
    second = map_label_artwork_to_zone(artwork, placement, fit_mode=fit_mode.lower())

    assert first == second
    assert first.zone_id == placement.zone_id
    assert first.placement_revision_id == placement.revision_id
    assert first.as_dict()["coordinate_unit"] == "unitless_normalized"
    assert first.as_dict()["geometry_authority_created"] is False
    assert all(0.0 <= value <= 1.0 for value in first.target_rect_normalized_uv)
    if fit_mode == "CONTAIN":
        assert first.target_rect_normalized_uv[3] - first.target_rect_normalized_uv[1] < (
            placement.boundary.v_max - placement.boundary.v_min
        )
        assert first.source_crop_rect == (0.0, 0.0, 200.0, 100.0)
    elif fit_mode == "COVER":
        assert first.source_crop_rect[2] - first.source_crop_rect[0] < artwork.width


def test_artwork_replacement_changes_only_presentation_mapping_not_zone_revision() -> None:
    placement = _placement()
    before = placement.as_dict()
    first_asset = ingest_label_artwork(_svg("red"))
    replacement_asset = ingest_label_artwork(_svg("blue"))

    first_mapping = map_label_artwork_to_zone(first_asset, placement)
    replacement_mapping = map_label_artwork_to_zone(replacement_asset, placement)

    assert first_asset.revision_id != replacement_asset.revision_id
    assert first_mapping.revision_id != replacement_mapping.revision_id
    assert replacement_mapping.zone_id == placement.zone_id
    assert replacement_mapping.placement_revision_id == placement.revision_id
    assert placement.as_dict() == before


def test_unsupported_fit_and_path_like_source_types_reject() -> None:
    placement = _placement()
    artwork = ingest_label_artwork(_svg())
    with pytest.raises(LabelArtworkError, match="fit_mode_unsupported"):
        map_label_artwork_to_zone(artwork, placement, fit_mode="tile")
    with pytest.raises(LabelArtworkError, match="source_type_invalid"):
        ingest_label_artwork(object())  # type: ignore[arg-type]
