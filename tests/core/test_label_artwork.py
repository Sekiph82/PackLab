from __future__ import annotations

import hashlib
import json
import struct
import zlib

import pytest
from tests.core.test_label_zone_placement import _zone

from packlab_core.label_artwork import (
    LabelArtworkError,
    create_label_artwork_assignment,
    ingest_label_artwork,
    map_label_artwork_to_zone,
    remove_label_artwork_assignment,
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


def _placement(kind: LabelZoneKind = LabelZoneKind.FRONT):
    _, _, zone = _zone(kind)
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


@pytest.mark.parametrize("kind", [LabelZoneKind.FRONT, LabelZoneKind.BACK])
def test_front_and_back_variants_bind_independently_to_exact_zone_revisions(
    kind: LabelZoneKind,
) -> None:
    placement = _placement(kind)
    artwork = ingest_label_artwork(_svg(kind.value))
    mapping = map_label_artwork_to_zone(artwork, placement)
    before_zone = placement.label_zone.as_dict()
    before_placement = placement.as_dict()

    first = create_label_artwork_assignment(mapping, placement, variant_id=f"{kind.value}-primary")
    repeated = create_label_artwork_assignment(
        mapping, placement, variant_id=f"{kind.value}-primary"
    )

    assert first == repeated
    assert first.zone_kind == kind.value
    assert first.zone_id == placement.zone_id
    assert first.placement_revision_id == placement.revision_id
    assert first.artwork_revision_id == artwork.revision_id
    assert first.as_dict()["mutates_source_geometry"] is False
    assert placement.label_zone.as_dict() == before_zone
    assert placement.as_dict() == before_placement


def test_front_and_back_variants_can_coexist_for_distinct_zone_ids() -> None:
    artwork = ingest_label_artwork(_svg())
    front = _placement(LabelZoneKind.FRONT)
    back = _placement(LabelZoneKind.BACK)
    front_assignment = create_label_artwork_assignment(
        map_label_artwork_to_zone(artwork, front), front, variant_id="campaign-front"
    )
    back_assignment = create_label_artwork_assignment(
        map_label_artwork_to_zone(artwork, back), back, variant_id="campaign-back"
    )

    assert front_assignment.zone_id != back_assignment.zone_id
    assert front_assignment.variant_id != back_assignment.variant_id
    assert front_assignment.revision_id != back_assignment.revision_id


def test_wrap_assignment_requires_normalized_seam_and_persists_orientation() -> None:
    placement = _placement(LabelZoneKind.WRAP)
    artwork = ingest_label_artwork(_svg())
    mapping = map_label_artwork_to_zone(artwork, placement)

    with pytest.raises(LabelArtworkError, match="wrap_seam_required_or_invalid"):
        create_label_artwork_assignment(mapping, placement, variant_id="wrap-primary")
    assignment = create_label_artwork_assignment(
        mapping,
        placement,
        variant_id="wrap-primary",
        wrap_seam_u_normalized=0.875,
        orientation="REVERSED_U",
    )

    assert assignment.zone_kind == "wrap"
    assert assignment.wrap_seam_u_normalized == 0.875
    assert assignment.orientation == "REVERSED_U"
    assert assignment.as_dict()["coordinate_unit"] == "unitless_normalized"
    assert assignment.as_dict()["physical_fit_verified"] is False


@pytest.mark.parametrize("seam", [-0.01, 1.0, float("nan"), True])
def test_wrap_assignment_rejects_invalid_seam(seam: float) -> None:
    placement = _placement(LabelZoneKind.WRAP)
    mapping = map_label_artwork_to_zone(ingest_label_artwork(_svg()), placement)
    with pytest.raises(LabelArtworkError, match="wrap_seam_required_or_invalid"):
        create_label_artwork_assignment(
            mapping, placement, variant_id="wrap-primary", wrap_seam_u_normalized=seam
        )


def test_assignment_rejects_stale_mapping_wrong_zone_kind_and_invalid_orientation() -> None:
    artwork = ingest_label_artwork(_svg())
    front = _placement(LabelZoneKind.FRONT)
    back = _placement(LabelZoneKind.BACK)
    stale = map_label_artwork_to_zone(artwork, front)
    with pytest.raises(LabelArtworkError, match="stale_or_wrong_zone"):
        create_label_artwork_assignment(stale, back, variant_id="back-primary")
    back_mapping = map_label_artwork_to_zone(artwork, back)
    with pytest.raises(LabelArtworkError, match="wrap_seam_wrong_zone_kind"):
        create_label_artwork_assignment(
            back_mapping, back, variant_id="back-primary", wrap_seam_u_normalized=0.25
        )
    with pytest.raises(LabelArtworkError, match="orientation_invalid"):
        create_label_artwork_assignment(
            back_mapping, back, variant_id="back-primary", orientation="SIDEWAYS"
        )


def test_variant_replacement_and_removal_create_reversible_successors() -> None:
    placement = _placement()
    zone_before = placement.label_zone.as_dict()
    original_mapping = map_label_artwork_to_zone(ingest_label_artwork(_svg("red")), placement)
    replacement_mapping = map_label_artwork_to_zone(ingest_label_artwork(_svg("blue")), placement)
    original = create_label_artwork_assignment(
        original_mapping, placement, variant_id="campaign-front"
    )
    replacement = create_label_artwork_assignment(
        replacement_mapping,
        placement,
        variant_id="campaign-front",
        previous=original,
    )
    removed = remove_label_artwork_assignment(replacement)

    assert replacement.previous_revision_id == original.revision_id
    assert replacement.artwork_revision_id != original.artwork_revision_id
    assert removed.status == "REMOVED"
    assert removed.mapping_revision_id is None
    assert removed.artwork_revision_id is None
    assert removed.previous_revision_id == replacement.revision_id
    assert original.status == replacement.status == "ASSIGNED"
    assert placement.label_zone.as_dict() == zone_before


def test_assignment_replacement_cannot_retarget_another_variant_or_zone() -> None:
    placement = _placement()
    mapping = map_label_artwork_to_zone(ingest_label_artwork(_svg()), placement)
    original = create_label_artwork_assignment(mapping, placement, variant_id="front-a")
    with pytest.raises(LabelArtworkError, match="previous_assignment_mismatch"):
        create_label_artwork_assignment(mapping, placement, variant_id="front-b", previous=original)


def test_metric_host_size_keeps_artwork_aspect_in_millimetres() -> None:
    # Review O-1: CONTAIN/COVER used normalized zone units, stretching square artwork on a
    # 70 x 28 mm zone. With the host face size the drawn artwork keeps its true aspect.
    from packlab_core.label_artwork import map_label_artwork_to_zone

    artwork, placement = _square_artwork_and_wide_placement()
    host = (100.0, 40.0)  # mm_unverified host face; zone = boundary fraction of it
    boundary = placement.boundary
    zone_mm = (
        (boundary.u_max - boundary.u_min) * host[0],
        (boundary.v_max - boundary.v_min) * host[1],
    )
    contain = map_label_artwork_to_zone(
        artwork, placement, fit_mode="CONTAIN", host_size_mm_unverified=host
    )
    u0, v0, u1, v1 = contain.target_rect_normalized_uv
    drawn_mm = ((u1 - u0) * host[0], (v1 - v0) * host[1])
    assert abs(drawn_mm[0] / drawn_mm[1] - artwork.width / artwork.height) < 1e-9
    assert drawn_mm[0] <= zone_mm[0] + 1e-9 and drawn_mm[1] <= zone_mm[1] + 1e-9
    assert contain.as_dict()["aspect_basis"] == "METRIC_ZONE_MM_UNVERIFIED"

    cover = map_label_artwork_to_zone(
        artwork, placement, fit_mode="COVER", host_size_mm_unverified=host
    )
    cu0, cv0, cu1, cv1 = cover.source_crop_rect
    zone_aspect = zone_mm[0] / zone_mm[1]
    assert abs((cu1 - cu0) / (cv1 - cv0) - zone_aspect) < 1e-9


_SEVEN_BY_THREE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="7" height="3" '
    b'viewBox="0 0 7 3"><rect width="7" height="3" fill="blue"/></svg>'
)
GOLDEN_DEFAULT_MAPPING_IDS = {
    # Computed with the module as of e97d4027^ (before the metric-aspect option).
    (
        "svg",
        "CONTAIN",
    ): "label-artwork-mapping:0f6cb3cdd7da39e852443a114ad64e197fd664702f1d09ba9cfd927f5aa5399d",
    (
        "svg",
        "COVER",
    ): "label-artwork-mapping:5ff55760eb2ec9db4abb0652b0d3df45988570821ea89c5d3c1ac43a55acb229",
    (
        "svg",
        "STRETCH",
    ): "label-artwork-mapping:0ee2c9c7810fae404f94d2d07333f08111a5dfda6adcce20e604a1a8453f6135",
    (
        "png",
        "CONTAIN",
    ): "label-artwork-mapping:0a4d025cd5caeedab21da4788115cab451083a646515a0b69a00df49e1d4cab8",
    (
        "png",
        "COVER",
    ): "label-artwork-mapping:6ff3c41a0515c7920d6e978a38e75aa688ecce6dc3a3b1c442ef801058381956",
    (
        "png",
        "STRETCH",
    ): "label-artwork-mapping:34348220a0ded6d3fd522ae7346fac248be8f049033baeace96661de98e3b1ff",
}
# 7x3 artwork: drawn_height/height differs from drawn_width/width in the last float bit,
# so these pin the historical uniform default scale (review V02 N-2).
GOLDEN_DEFAULT_MAPPING_IDS.update(
    {
        (
            "7x3",
            "CONTAIN",
        ): "label-artwork-mapping:caaaa12594b621e362ecce0026754d81050a433ba5ad8dc6c310b7501b637f87",
        (
            "7x3",
            "COVER",
        ): "label-artwork-mapping:31c817209b4148d0959fcdf7fd96a24023b0936abaa2d37e544ac023e72c8fc3",
    }
)


@pytest.mark.parametrize(("kind", "fit"), sorted(GOLDEN_DEFAULT_MAPPING_IDS))
def test_default_mapping_ids_match_the_pre_change_golden_values(kind: str, fit: str) -> None:
    # Review P2-2: pins historical ids; the default path must not drift.
    from packlab_core.label_artwork import ingest_label_artwork, map_label_artwork_to_zone

    content = {"svg": _svg(), "png": _png(), "7x3": _SEVEN_BY_THREE_SVG}[kind]
    artwork = ingest_label_artwork(content)
    mapping = map_label_artwork_to_zone(artwork, _placement(), fit_mode=fit)
    assert mapping.revision_id == GOLDEN_DEFAULT_MAPPING_IDS[(kind, fit)]
    assert "aspect_basis" not in mapping.as_dict()  # keeps overlay/scene digests unchanged


def test_metric_and_default_mappings_have_distinct_ids_and_reject_bad_host_sizes() -> None:
    from packlab_core.label_artwork import LabelArtworkError, map_label_artwork_to_zone

    artwork, placement = _square_artwork_and_wide_placement()
    default = map_label_artwork_to_zone(artwork, placement, fit_mode="CONTAIN")
    # A unit host gives the same geometry as the default, but the basis differs, so the id must.
    same_shape = map_label_artwork_to_zone(
        artwork, placement, fit_mode="CONTAIN", host_size_mm_unverified=(1.0, 1.0)
    )
    assert same_shape.revision_id != default.revision_id
    bad_hosts = (
        (0.0, 1.0),
        (1.0,),
        (float("nan"), 1.0),
        (True, 1.0),
        (5e-324, 1.0),
        (1e-300, 1e300),
        (1e300, 1e-300),
    )
    for bad in bad_hosts:
        # Extreme ratios may instead trip the mapping's own validity check; either way it is
        # the module's error, never an uncaught ZeroDivisionError (review P3-2). Each fit
        # mode is checked on its own (review V02 N-1).
        for fit in ("CONTAIN", "COVER"):
            with pytest.raises(LabelArtworkError, match="host_size_invalid|mapping_invalid"):
                map_label_artwork_to_zone(
                    artwork,
                    placement,
                    fit_mode=fit,
                    host_size_mm_unverified=bad,  # type: ignore[arg-type]
                )


@pytest.mark.parametrize(
    ("host", "fit"),
    [
        ((100.0, 40.0), "CONTAIN"),  # wide zone: height-limited branch
        ((20.0, 400.0), "CONTAIN"),  # tall zone: width-limited branch
        ((100.0, 40.0), "COVER"),
        ((20.0, 400.0), "COVER"),
    ],
)
def test_metric_mapping_draws_with_equal_millimetre_scale_and_exact_transform(host, fit) -> None:
    # Review P2-1: guard the scale/translate values the renderer actually draws with.
    from packlab_core.label_artwork import map_label_artwork_to_zone

    artwork, placement = _square_artwork_and_wide_placement()
    mapping = map_label_artwork_to_zone(
        artwork, placement, fit_mode=fit, host_size_mm_unverified=host
    )
    c0, c1, c2, c3 = mapping.source_crop_rect
    t0, t1, t2, t3 = mapping.target_rect_normalized_uv
    # crop * scale + translate == target, on both axes.
    assert c0 * mapping.scale_u + mapping.translate_u == pytest.approx(t0)
    assert c2 * mapping.scale_u + mapping.translate_u == pytest.approx(t2)
    assert c1 * mapping.scale_v + mapping.translate_v == pytest.approx(t1)
    assert c3 * mapping.scale_v + mapping.translate_v == pytest.approx(t3)
    # One source unit spans the same millimetres horizontally and vertically.
    assert mapping.scale_u * host[0] == pytest.approx(mapping.scale_v * host[1])
    boundary = placement.boundary
    if fit == "CONTAIN":
        assert boundary.u_min - 1e-12 <= t0 and t2 <= boundary.u_max + 1e-12
        assert boundary.v_min - 1e-12 <= t1 and t3 <= boundary.v_max + 1e-12
        # Centred inside the boundary.
        assert (t0 + t2) / 2 == pytest.approx((boundary.u_min + boundary.u_max) / 2)
        assert (t1 + t3) / 2 == pytest.approx((boundary.v_min + boundary.v_max) / 2)
    else:
        assert 0.0 <= c0 and c2 <= artwork.width and 0.0 <= c1 and c3 <= artwork.height
        assert (c0 + c2) / 2 == pytest.approx(artwork.width / 2)
        assert (c1 + c3) / 2 == pytest.approx(artwork.height / 2)


def _square_artwork_and_wide_placement():
    from packlab_core.label_artwork import ingest_label_artwork

    square = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        b'viewBox="0 0 100 100"><rect width="100" height="100" fill="red"/></svg>'
    )
    return ingest_label_artwork(square), _placement()
