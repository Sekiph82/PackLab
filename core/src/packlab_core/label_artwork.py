"""Bounded offline artwork assets and reversible Label Zone presentation mappings."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from .label_zone_placement import LabelZonePlacementRevision

LABEL_ARTWORK_ASSET_CONTRACT = "packlab.label-artwork-asset.v1"
LABEL_ARTWORK_MAPPING_CONTRACT = "packlab.label-artwork-mapping.v1"
MAX_ARTWORK_BYTES = 8 * 1024 * 1024
MAX_SVG_NODES = 50_000
MAX_SVG_DEPTH = 64
MAX_PNG_DIMENSION = 16_384
MAX_PNG_PIXELS = 32_000_000
MAX_PNG_DECODED_BYTES = 64 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VARIANT_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_LENGTH = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)(?:px)?\s*$", re.IGNORECASE)


class LabelArtworkError(ValueError):
    """Raised when local artwork is unsafe, malformed, or cannot be mapped."""


@dataclass(frozen=True, slots=True)
class LabelArtworkAssetRevision:
    revision_id: str
    content_sha256: str
    media_type: str
    byte_size: int
    width: float
    height: float
    coordinate_unit: str
    contract: str = LABEL_ARTWORK_ASSET_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != LABEL_ARTWORK_ASSET_CONTRACT
            or not _SHA256.fullmatch(self.content_sha256)
            or self.media_type not in {"image/svg+xml", "image/png"}
            or isinstance(self.byte_size, bool)
            or not isinstance(self.byte_size, int)
            or not 1 <= self.byte_size <= MAX_ARTWORK_BYTES
            or self.coordinate_unit != "source_artwork_units"
            or not math.isfinite(self.width)
            or not math.isfinite(self.height)
            or self.width <= 0.0
            or self.height <= 0.0
            or self.revision_id != "label-artwork:" + _asset_digest(self)
        ):
            raise LabelArtworkError("label_artwork_asset_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "PRESENTATION_ARTWORK_ASSET",
            "revision_id": self.revision_id,
            "content_sha256": self.content_sha256,
            "media_type": self.media_type,
            "byte_size": self.byte_size,
            "intrinsic_width": self.width,
            "intrinsic_height": self.height,
            "coordinate_unit": self.coordinate_unit,
            "changes_design_model": False,
            "changes_cad_brep": False,
            "changes_label_zone": False,
            "remote_fetch_performed": False,
        }


@dataclass(frozen=True, slots=True)
class LabelArtworkMappingRevision:
    revision_id: str
    source_artwork_revision_id: str
    source_artwork_sha256: str
    zone_id: str
    placement_revision_id: str
    fit_mode: str
    target_rect_normalized_uv: tuple[float, float, float, float]
    source_crop_rect: tuple[float, float, float, float]
    scale_u: float
    scale_v: float
    translate_u: float
    translate_v: float
    contract: str = LABEL_ARTWORK_MAPPING_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != LABEL_ARTWORK_MAPPING_CONTRACT
            or not _SHA256.fullmatch(self.source_artwork_sha256)
            or self.fit_mode not in {"CONTAIN", "COVER", "STRETCH"}
            or not self.source_artwork_revision_id
            or not self.zone_id
            or not self.placement_revision_id
            or not all(
                math.isfinite(value)
                for value in (
                    *self.target_rect_normalized_uv,
                    *self.source_crop_rect,
                    self.scale_u,
                    self.scale_v,
                    self.translate_u,
                    self.translate_v,
                )
            )
            or self.scale_u <= 0.0
            or self.scale_v <= 0.0
            or self.revision_id != "label-artwork-mapping:" + _mapping_digest(self)
        ):
            raise LabelArtworkError("label_artwork_mapping_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "REVERSIBLE_LABEL_ZONE_PRESENTATION_MAPPING",
            "revision_id": self.revision_id,
            "source_artwork_revision_id": self.source_artwork_revision_id,
            "source_artwork_sha256": self.source_artwork_sha256,
            "zone_id": self.zone_id,
            "placement_revision_id": self.placement_revision_id,
            "fit_mode": self.fit_mode,
            "coordinate_frame": "LABEL_ZONE_NORMALIZED_UV",
            "coordinate_unit": "unitless_normalized",
            "target_rect_normalized_uv": list(self.target_rect_normalized_uv),
            "source_crop_rect": list(self.source_crop_rect),
            "source_crop_coordinate_unit": "source_artwork_units",
            "transform_scale_unit": "unitless_normalized_per_source_artwork_unit",
            "scale_u": self.scale_u,
            "scale_v": self.scale_v,
            "translate_u": self.translate_u,
            "translate_v": self.translate_v,
            "geometry_authority_created": False,
            "physical_fit_verified": False,
        }


LABEL_ARTWORK_ASSIGNMENT_CONTRACT = "packlab.label-artwork-assignment.v1"


@dataclass(frozen=True, slots=True)
class LabelArtworkAssignmentRevision:
    """Immutable, reversible presentation assignment for one exact zone variant."""

    revision_id: str
    variant_id: str
    zone_id: str
    zone_kind: str
    placement_revision_id: str
    mapping_revision_id: str | None
    artwork_revision_id: str | None
    status: str
    wrap_seam_u_normalized: float | None
    orientation: str
    previous_revision_id: str | None
    contract: str = LABEL_ARTWORK_ASSIGNMENT_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != LABEL_ARTWORK_ASSIGNMENT_CONTRACT
            or not isinstance(self.variant_id, str)
            or not _VARIANT_ID.fullmatch(self.variant_id)
            or self.zone_kind not in {"front", "back", "wrap"}
            or not isinstance(self.zone_id, str)
            or not self.zone_id
            or not isinstance(self.placement_revision_id, str)
            or not self.placement_revision_id
            or self.status not in {"ASSIGNED", "REMOVED"}
            or self.orientation not in {"CANONICAL_UV", "REVERSED_U"}
            or (
                self.previous_revision_id is not None
                and (
                    not isinstance(self.previous_revision_id, str) or not self.previous_revision_id
                )
            )
            or (
                self.status == "ASSIGNED"
                and (not self.mapping_revision_id or not self.artwork_revision_id)
            )
            or (
                self.status == "REMOVED"
                and (self.mapping_revision_id is not None or self.artwork_revision_id is not None)
            )
            or (
                self.zone_kind == "wrap"
                and (
                    self.wrap_seam_u_normalized is None
                    or isinstance(self.wrap_seam_u_normalized, bool)
                    or not isinstance(self.wrap_seam_u_normalized, (int, float))
                    or not math.isfinite(self.wrap_seam_u_normalized)
                    or not 0.0 <= self.wrap_seam_u_normalized < 1.0
                )
            )
            or (self.zone_kind != "wrap" and self.wrap_seam_u_normalized is not None)
            or self.revision_id != "label-artwork-assignment:" + _assignment_digest(self)
        ):
            raise LabelArtworkError("label_artwork_assignment_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "REVERSIBLE_LABEL_ZONE_PRESENTATION_ASSIGNMENT",
            "revision_id": self.revision_id,
            "variant_id": self.variant_id,
            "zone_id": self.zone_id,
            "zone_kind": self.zone_kind,
            "placement_revision_id": self.placement_revision_id,
            "mapping_revision_id": self.mapping_revision_id,
            "artwork_revision_id": self.artwork_revision_id,
            "status": self.status,
            "wrap_seam_u_normalized": self.wrap_seam_u_normalized,
            "orientation": self.orientation,
            "previous_revision_id": self.previous_revision_id,
            "coordinate_unit": "unitless_normalized",
            "mutates_source_geometry": False,
            "changes_label_zone": False,
            "physical_fit_verified": False,
        }


def create_label_artwork_assignment(
    mapping: LabelArtworkMappingRevision,
    placement: LabelZonePlacementRevision,
    *,
    variant_id: str,
    wrap_seam_u_normalized: float | None = None,
    orientation: str = "CANONICAL_UV",
    previous: LabelArtworkAssignmentRevision | None = None,
) -> LabelArtworkAssignmentRevision:
    """Bind one mapping to an exact front, back, or wrap placement variant."""
    if not isinstance(mapping, LabelArtworkMappingRevision):
        raise LabelArtworkError("label_artwork_mapping_required")
    if not isinstance(placement, LabelZonePlacementRevision):
        raise LabelArtworkError("label_artwork_zone_placement_required")
    zone = placement.label_zone
    if (
        mapping.zone_id != placement.zone_id
        or mapping.placement_revision_id != placement.revision_id
    ):
        raise LabelArtworkError("label_artwork_assignment_stale_or_wrong_zone")
    if not isinstance(variant_id, str) or not _VARIANT_ID.fullmatch(variant_id):
        raise LabelArtworkError("label_artwork_variant_id_invalid")
    if previous is not None:
        if not isinstance(previous, LabelArtworkAssignmentRevision):
            raise LabelArtworkError("label_artwork_previous_assignment_invalid")
        if previous.status != "ASSIGNED" or (
            previous.variant_id,
            previous.zone_id,
            previous.zone_kind,
        ) != (variant_id, placement.zone_id, zone.zone_kind.value):
            raise LabelArtworkError("label_artwork_previous_assignment_mismatch")
    if zone.zone_kind.value == "wrap":
        if (
            isinstance(wrap_seam_u_normalized, bool)
            or not isinstance(wrap_seam_u_normalized, (int, float))
            or not math.isfinite(wrap_seam_u_normalized)
            or not 0.0 <= wrap_seam_u_normalized < 1.0
        ):
            raise LabelArtworkError("label_artwork_wrap_seam_required_or_invalid")
    elif wrap_seam_u_normalized is not None:
        raise LabelArtworkError("label_artwork_wrap_seam_wrong_zone_kind")
    if not isinstance(orientation, str) or orientation not in {"CANONICAL_UV", "REVERSED_U"}:
        raise LabelArtworkError("label_artwork_orientation_invalid")
    values: dict[str, object] = {
        "contract": LABEL_ARTWORK_ASSIGNMENT_CONTRACT,
        "variant_id": variant_id,
        "zone_id": placement.zone_id,
        "zone_kind": zone.zone_kind.value,
        "placement_revision_id": placement.revision_id,
        "mapping_revision_id": mapping.revision_id,
        "artwork_revision_id": mapping.source_artwork_revision_id,
        "status": "ASSIGNED",
        "wrap_seam_u_normalized": wrap_seam_u_normalized,
        "orientation": orientation,
        "previous_revision_id": previous.revision_id if previous is not None else None,
    }
    return LabelArtworkAssignmentRevision(
        revision_id="label-artwork-assignment:" + _digest(values),
        variant_id=variant_id,
        zone_id=placement.zone_id,
        zone_kind=zone.zone_kind.value,
        placement_revision_id=placement.revision_id,
        mapping_revision_id=mapping.revision_id,
        artwork_revision_id=mapping.source_artwork_revision_id,
        status="ASSIGNED",
        wrap_seam_u_normalized=wrap_seam_u_normalized,
        orientation=orientation,
        previous_revision_id=previous.revision_id if previous is not None else None,
    )


def remove_label_artwork_assignment(
    previous: LabelArtworkAssignmentRevision,
) -> LabelArtworkAssignmentRevision:
    """Create an immutable removal revision; earlier assignment remains addressable."""
    if not isinstance(previous, LabelArtworkAssignmentRevision) or previous.status != "ASSIGNED":
        raise LabelArtworkError("label_artwork_active_assignment_required")
    values: dict[str, object] = {
        "contract": LABEL_ARTWORK_ASSIGNMENT_CONTRACT,
        "variant_id": previous.variant_id,
        "zone_id": previous.zone_id,
        "zone_kind": previous.zone_kind,
        "placement_revision_id": previous.placement_revision_id,
        "mapping_revision_id": None,
        "artwork_revision_id": None,
        "status": "REMOVED",
        "wrap_seam_u_normalized": previous.wrap_seam_u_normalized,
        "orientation": previous.orientation,
        "previous_revision_id": previous.revision_id,
    }
    return LabelArtworkAssignmentRevision(
        revision_id="label-artwork-assignment:" + _digest(values),
        variant_id=previous.variant_id,
        zone_id=previous.zone_id,
        zone_kind=previous.zone_kind,
        placement_revision_id=previous.placement_revision_id,
        mapping_revision_id=None,
        artwork_revision_id=None,
        status="REMOVED",
        wrap_seam_u_normalized=previous.wrap_seam_u_normalized,
        orientation=previous.orientation,
        previous_revision_id=previous.revision_id,
    )


def ingest_label_artwork(
    source: bytes | bytearray | memoryview | str | Path,
) -> LabelArtworkAssetRevision:
    """Validate bounded local SVG/PNG content; never persist the supplied path."""
    content = _read_bounded_source(source)
    digest = hashlib.sha256(content).hexdigest()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        media_type = "image/png"
        width, height = _validate_png(content)
    else:
        media_type = "image/svg+xml"
        width, height = _validate_svg(content)
    identity = {
        "contract": LABEL_ARTWORK_ASSET_CONTRACT,
        "content_sha256": digest,
        "media_type": media_type,
        "byte_size": len(content),
        "width": width,
        "height": height,
        "coordinate_unit": "source_artwork_units",
    }
    return LabelArtworkAssetRevision(
        "label-artwork:" + _digest(identity),
        digest,
        media_type,
        len(content),
        width,
        height,
        "source_artwork_units",
    )


def map_label_artwork_to_zone(
    artwork: LabelArtworkAssetRevision,
    placement: LabelZonePlacementRevision,
    *,
    fit_mode: str = "CONTAIN",
) -> LabelArtworkMappingRevision:
    """Map artwork to exact placement intent in normalized UV without changing geometry."""
    if not isinstance(artwork, LabelArtworkAssetRevision):
        raise LabelArtworkError("label_artwork_asset_required")
    if not isinstance(placement, LabelZonePlacementRevision):
        raise LabelArtworkError("label_artwork_zone_placement_required")
    if not isinstance(fit_mode, str) or fit_mode.upper() not in {"CONTAIN", "COVER", "STRETCH"}:
        raise LabelArtworkError("label_artwork_fit_mode_unsupported")
    fit = fit_mode.upper()
    boundary = placement.boundary
    target_width, target_height = boundary.u_max - boundary.u_min, boundary.v_max - boundary.v_min
    source_aspect = artwork.width / artwork.height
    target_aspect = target_width / target_height
    if fit == "STRETCH":
        target = (boundary.u_min, boundary.v_min, boundary.u_max, boundary.v_max)
        crop = (0.0, 0.0, artwork.width, artwork.height)
        scale_u, scale_v = target_width / artwork.width, target_height / artwork.height
    elif fit == "CONTAIN":
        if source_aspect >= target_aspect:
            drawn_width = target_width
            drawn_height = target_width / source_aspect
        else:
            drawn_height = target_height
            drawn_width = target_height * source_aspect
        u0 = boundary.u_min + (target_width - drawn_width) / 2.0
        v0 = boundary.v_min + (target_height - drawn_height) / 2.0
        target = (u0, v0, u0 + drawn_width, v0 + drawn_height)
        crop = (0.0, 0.0, artwork.width, artwork.height)
        scale_u = scale_v = drawn_width / artwork.width
    else:
        if source_aspect >= target_aspect:
            crop_width = artwork.height * target_aspect
            crop = (
                (artwork.width - crop_width) / 2.0,
                0.0,
                (artwork.width + crop_width) / 2.0,
                artwork.height,
            )
        else:
            crop_height = artwork.width / target_aspect
            crop = (
                0.0,
                (artwork.height - crop_height) / 2.0,
                artwork.width,
                (artwork.height + crop_height) / 2.0,
            )
        target = (boundary.u_min, boundary.v_min, boundary.u_max, boundary.v_max)
        scale_u = target_width / (crop[2] - crop[0])
        scale_v = target_height / (crop[3] - crop[1])
    if not all(math.isfinite(value) for value in (*target, *crop, scale_u, scale_v)):
        raise LabelArtworkError("label_artwork_mapping_non_finite")
    translate_u = target[0] - crop[0] * scale_u
    translate_v = target[1] - crop[1] * scale_v
    values: dict[str, object] = {
        "contract": LABEL_ARTWORK_MAPPING_CONTRACT,
        "source_artwork_revision_id": artwork.revision_id,
        "source_artwork_sha256": artwork.content_sha256,
        "zone_id": placement.zone_id,
        "placement_revision_id": placement.revision_id,
        "fit_mode": fit,
        "target_rect_normalized_uv": list(target),
        "source_crop_rect": list(crop),
        "scale_u": scale_u,
        "scale_v": scale_v,
        "translate_u": translate_u,
        "translate_v": translate_v,
    }
    return LabelArtworkMappingRevision(
        "label-artwork-mapping:" + _digest(values),
        artwork.revision_id,
        artwork.content_sha256,
        placement.zone_id,
        placement.revision_id,
        fit,
        target,
        crop,
        scale_u,
        scale_v,
        translate_u,
        translate_v,
    )


def _read_bounded_source(source: bytes | bytearray | memoryview | str | Path) -> bytes:
    if isinstance(source, (bytes, bytearray, memoryview)):
        if not 1 <= len(source) <= MAX_ARTWORK_BYTES:
            raise LabelArtworkError("label_artwork_size_out_of_bounds")
        content = bytes(source)
    elif isinstance(source, (str, Path)):
        path = Path(source)
        try:
            if path.is_symlink() or not path.is_file():
                raise LabelArtworkError("label_artwork_local_file_required")
            size = path.stat().st_size
            if not 1 <= size <= MAX_ARTWORK_BYTES:
                raise LabelArtworkError("label_artwork_size_out_of_bounds")
            with path.open("rb") as stream:
                content = stream.read(MAX_ARTWORK_BYTES + 1)
        except LabelArtworkError:
            raise
        except OSError as error:
            raise LabelArtworkError("label_artwork_local_read_failed") from error
    else:
        raise LabelArtworkError("label_artwork_source_type_invalid")
    if not 1 <= len(content) <= MAX_ARTWORK_BYTES:
        raise LabelArtworkError("label_artwork_size_out_of_bounds")
    return content


def _validate_svg(content: bytes) -> tuple[float, float]:
    lowered = content.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered or b"<?xml-stylesheet" in lowered:
        raise LabelArtworkError("label_artwork_svg_doctype_forbidden")
    try:
        import xml.etree.ElementTree as et

        root = et.fromstring(content.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, ValueError, et.ParseError) as error:
        raise LabelArtworkError("label_artwork_svg_malformed") from error
    if root.tag.rsplit("}", 1)[-1].casefold() != "svg":
        raise LabelArtworkError("label_artwork_svg_root_invalid")
    nodes = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > MAX_SVG_NODES or depth > MAX_SVG_DEPTH:
            raise LabelArtworkError("label_artwork_svg_complexity_exceeded")
        tag = node.tag.rsplit("}", 1)[-1].casefold()
        if tag in {"script", "foreignobject", "image", "use", "iframe", "audio", "video", "link"}:
            raise LabelArtworkError("label_artwork_svg_active_or_external_content_forbidden")
        for key, value in node.attrib.items():
            key = key.rsplit("}", 1)[-1].casefold()
            lowered_value = value.casefold()
            if (
                key.startswith("on")
                or key in {"href", "src"}
                or "url(" in lowered_value
                or "@import" in lowered_value
            ):
                raise LabelArtworkError("label_artwork_svg_external_reference_forbidden")
        if node.text and ("url(" in node.text.casefold() or "@import" in node.text.casefold()):
            raise LabelArtworkError("label_artwork_svg_external_reference_forbidden")
        stack.extend((child, depth + 1) for child in node)
    view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if view_box:
        try:
            min_x, min_y, width, height = (
                float(item) for item in re.split(r"[\s,]+", view_box.strip())
            )
        except (ValueError, TypeError) as error:
            raise LabelArtworkError("label_artwork_svg_viewbox_invalid") from error
        if not math.isfinite(min_x) or not math.isfinite(min_y):
            raise LabelArtworkError("label_artwork_svg_viewbox_invalid")
    else:
        width = _svg_length(root.attrib.get("width"))
        height = _svg_length(root.attrib.get("height"))
    if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
        raise LabelArtworkError("label_artwork_svg_dimensions_invalid")
    return width, height


def _svg_length(value: str | None) -> float:
    if value is None:
        raise LabelArtworkError("label_artwork_svg_dimensions_required")
    match = _LENGTH.fullmatch(value)
    if not match:
        raise LabelArtworkError("label_artwork_svg_dimensions_invalid")
    return float(match.group(1))


def _validate_png(content: bytes) -> tuple[float, float]:
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise LabelArtworkError("label_artwork_png_signature_invalid")
    offset = 8
    chunk_count = 0
    width = height = color_type = bit_depth = None
    seen_idat = seen_iend = seen_plte = idat_closed = False
    compressed = bytearray()
    while offset < len(content):
        if offset + 12 > len(content):
            raise LabelArtworkError("label_artwork_png_chunk_truncated")
        length = struct.unpack_from(">I", content, offset)[0]
        chunk_type = content[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(content):
            raise LabelArtworkError("label_artwork_png_chunk_truncated")
        chunk_data = content[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack_from(">I", content, offset + 8 + length)[0]
        if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != expected_crc:
            raise LabelArtworkError("label_artwork_png_crc_invalid")
        chunk_count += 1
        if chunk_count > 10_000:
            raise LabelArtworkError("label_artwork_png_chunk_limit_exceeded")
        if chunk_count == 1:
            if chunk_type != b"IHDR" or length != 13:
                raise LabelArtworkError("label_artwork_png_ihdr_required")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if (
                not 1 <= width <= MAX_PNG_DIMENSION
                or not 1 <= height <= MAX_PNG_DIMENSION
                or width * height > MAX_PNG_PIXELS
                or bit_depth != 8
                or color_type not in {0, 2, 3, 4, 6}
                or compression != 0
                or filtering != 0
                or interlace != 0
            ):
                raise LabelArtworkError("label_artwork_png_format_unsupported")
        elif chunk_type == b"IHDR":
            raise LabelArtworkError("label_artwork_png_ihdr_duplicate")
        elif chunk_type == b"PLTE":
            if seen_idat or seen_plte or length == 0 or length > 768 or length % 3 != 0:
                raise LabelArtworkError("label_artwork_png_plte_invalid")
            seen_plte = True
        elif chunk_type == b"IDAT":
            if seen_iend or idat_closed:
                raise LabelArtworkError("label_artwork_png_chunk_order_invalid")
            seen_idat = True
            compressed.extend(chunk_data)
            if len(compressed) > MAX_ARTWORK_BYTES:
                raise LabelArtworkError("label_artwork_png_compressed_data_too_large")
        elif chunk_type == b"IEND":
            if length != 0 or not seen_idat:
                raise LabelArtworkError("label_artwork_png_iend_invalid")
            seen_iend = True
            offset = end
            if offset != len(content):
                raise LabelArtworkError("label_artwork_png_trailing_data")
            break
        elif chunk_type in {b"acTL", b"fcTL", b"fdAT"}:
            raise LabelArtworkError("label_artwork_png_animation_unsupported")
        elif seen_idat:
            idat_closed = True
        elif chunk_type[0] & 0x20 == 0 and chunk_type != b"IHDR":
            raise LabelArtworkError("label_artwork_png_critical_chunk_unsupported")
        offset = end
    if not seen_iend or width is None or height is None or color_type is None:
        raise LabelArtworkError("label_artwork_png_incomplete")
    if color_type == 3 and not seen_plte:
        raise LabelArtworkError("label_artwork_png_palette_required")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    expected_size = (1 + int(width) * channels) * int(height)
    if expected_size > MAX_PNG_DECODED_BYTES:
        raise LabelArtworkError("label_artwork_png_decoded_data_too_large")
    try:
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(bytes(compressed), expected_size + 1)
    except zlib.error as error:
        raise LabelArtworkError("label_artwork_png_idat_invalid") from error
    if len(decoded) != expected_size or not decoder.eof or decoder.unused_data:
        raise LabelArtworkError("label_artwork_png_idat_invalid")
    return float(width), float(height)


def _asset_digest(asset: LabelArtworkAssetRevision) -> str:
    value = {
        "contract": LABEL_ARTWORK_ASSET_CONTRACT,
        "content_sha256": asset.content_sha256,
        "media_type": asset.media_type,
        "byte_size": asset.byte_size,
        "width": asset.width,
        "height": asset.height,
        "coordinate_unit": asset.coordinate_unit,
    }
    return _digest(value)


def _mapping_digest(mapping: LabelArtworkMappingRevision) -> str:
    return _digest(
        {
            "contract": LABEL_ARTWORK_MAPPING_CONTRACT,
            "source_artwork_revision_id": mapping.source_artwork_revision_id,
            "source_artwork_sha256": mapping.source_artwork_sha256,
            "zone_id": mapping.zone_id,
            "placement_revision_id": mapping.placement_revision_id,
            "fit_mode": mapping.fit_mode,
            "target_rect_normalized_uv": list(mapping.target_rect_normalized_uv),
            "source_crop_rect": list(mapping.source_crop_rect),
            "scale_u": mapping.scale_u,
            "scale_v": mapping.scale_v,
            "translate_u": mapping.translate_u,
            "translate_v": mapping.translate_v,
        }
    )


def _assignment_digest(assignment: LabelArtworkAssignmentRevision) -> str:
    return _digest(
        {
            "contract": LABEL_ARTWORK_ASSIGNMENT_CONTRACT,
            "variant_id": assignment.variant_id,
            "zone_id": assignment.zone_id,
            "zone_kind": assignment.zone_kind,
            "placement_revision_id": assignment.placement_revision_id,
            "mapping_revision_id": assignment.mapping_revision_id,
            "artwork_revision_id": assignment.artwork_revision_id,
            "status": assignment.status,
            "wrap_seam_u_normalized": assignment.wrap_seam_u_normalized,
            "orientation": assignment.orientation,
            "previous_revision_id": assignment.previous_revision_id,
        }
    )


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "LABEL_ARTWORK_ASSET_CONTRACT",
    "LABEL_ARTWORK_ASSIGNMENT_CONTRACT",
    "LABEL_ARTWORK_MAPPING_CONTRACT",
    "LabelArtworkAssetRevision",
    "LabelArtworkAssignmentRevision",
    "LabelArtworkError",
    "LabelArtworkMappingRevision",
    "create_label_artwork_assignment",
    "ingest_label_artwork",
    "map_label_artwork_to_zone",
    "remove_label_artwork_assignment",
]
