"""Deterministic, bounded post-processing for PackLab mask artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from .segmentation import (
    CoordinateTransform,
    MaskArtifact,
    MaskRaster,
    SegmentationContractError,
)

MASK_POSTPROCESSING_PIPELINE_ID = "packlab.mask-post-processing"
MASK_POSTPROCESSING_PIPELINE_VERSION = "1.0.0"
MASK_CONNECTIVITY = 4
MAX_AREA_THRESHOLD = 1_000_000


class MaskPostProcessingError(SegmentationContractError):
    """Raised when a parent mask or bounded processing request is invalid."""


@dataclass(frozen=True, slots=True)
class MaskPostProcessingParameters:
    """Explicit pixel-area thresholds; zero disables each area operation."""

    max_hole_area: int = 0
    max_component_area_to_remove: int = 0
    fill_single_pixel_notches: bool = False

    def __post_init__(self) -> None:
        for name in ("max_hole_area", "max_component_area_to_remove"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise MaskPostProcessingError(f"{name} must be a non-negative integer")
            if value > MAX_AREA_THRESHOLD:
                raise MaskPostProcessingError(
                    f"{name} cannot exceed the project limit of {MAX_AREA_THRESHOLD} pixels"
                )
        if not isinstance(self.fill_single_pixel_notches, bool):
            raise MaskPostProcessingError("fill_single_pixel_notches must be a boolean")

    def as_dict(self) -> dict[str, object]:
        return {
            "max_hole_area": self.max_hole_area,
            "max_component_area_to_remove": self.max_component_area_to_remove,
            "fill_single_pixel_notches": self.fill_single_pixel_notches,
        }


@dataclass(frozen=True, slots=True)
class MaskPostProcessingResult:
    parent: MaskArtifact
    child: MaskArtifact


def post_process_mask(
    parent: MaskArtifact,
    parameters: MaskPostProcessingParameters,
) -> MaskPostProcessingResult:
    """Create an immutable child revision from an in-memory parent raster.

    Components and holes use 4-connectivity. Holes of area <= max_hole_area
    are filled; foreground components of area <= max_component_area_to_remove
    are removed. Edge cleanup is a single synchronous pass that fills interior
    background pixels with exactly three foreground cardinal neighbors.
    Image-boundary pixels are never changed by edge cleanup.
    """
    if not isinstance(parent, MaskArtifact):
        raise MaskPostProcessingError("parent must be a MaskArtifact")
    if not isinstance(parameters, MaskPostProcessingParameters):
        raise MaskPostProcessingError("parameters must be MaskPostProcessingParameters")
    raster = parent.raster
    if raster is None:
        raise MaskPostProcessingError("parent mask raster is required for post-processing")
    # Bind this consumer to the exact in-memory bytes before copying or deriving anything.
    if raster.digest != parent.mask_digest:
        raise MaskPostProcessingError(
            "parent mask raster digest does not match the declared mask_digest"
        )
    if (raster.width, raster.height) != (parent.mask_width, parent.mask_height):
        raise MaskPostProcessingError("parent raster dimensions do not match mask dimensions")
    pixel_count = raster.width * raster.height
    if parameters.max_hole_area > pixel_count:
        raise MaskPostProcessingError("max_hole_area exceeds parent mask dimensions")
    if parameters.max_component_area_to_remove > pixel_count:
        raise MaskPostProcessingError("component area threshold exceeds parent mask dimensions")

    values = list(raster.values)
    before_count = sum(values)
    holes_filled, hole_pixels = _fill_small_holes(
        values, raster.width, raster.height, parameters.max_hole_area
    )
    edge_pixels = (
        _fill_single_pixel_notches(values, raster.width, raster.height)
        if parameters.fill_single_pixel_notches
        else 0
    )
    components_removed, component_pixels = _remove_small_components(
        values, raster.width, raster.height, parameters.max_component_area_to_remove
    )
    output = MaskRaster(raster.width, raster.height, tuple(values))
    after_count = sum(output.values)
    transform = CoordinateTransform(
        parent.transform.source_width,
        parent.transform.source_height,
        parent.transform.model_width,
        parent.transform.model_height,
        parent.transform.scale_x,
        parent.transform.scale_y,
        parent.transform.offset_x,
        parent.transform.offset_y,
        parent.transform.interpolation,
    )
    parameters_dict = parameters.as_dict()
    identity: dict[str, object] = {
        "parent_artifact_id": parent.artifact_id,
        "parent_mask_revision": parent.mask_revision,
        "parent_mask_digest": parent.mask_digest,
        "source_image_asset_id": parent.source_image_asset_id,
        "source_digest": parent.source_digest,
        "source_dimensions": {"width": parent.source_width, "height": parent.source_height},
        "source_transform": transform.as_dict(),
        "pipeline_id": MASK_POSTPROCESSING_PIPELINE_ID,
        "pipeline_version": MASK_POSTPROCESSING_PIPELINE_VERSION,
        "parameters": parameters_dict,
        "mask_digest": output.digest,
    }
    identity_digest = _canonical_digest(identity)
    evidence = {
        **identity,
        "identity_sha256": identity_digest,
        "connectivity": MASK_CONNECTIVITY,
        "hole_rule": "fill enclosed 4-connected background components with area <= max_hole_area",
        "component_rule": "remove 4-connected foreground components with area <= max_component_area_to_remove",
        "edge_cleanup_rule": (
            "one synchronous pass; fill interior background pixel with exactly three foreground cardinal neighbors; preserve image boundary"
            if parameters.fill_single_pixel_notches
            else "disabled"
        ),
        "foreground_pixels_before": before_count,
        "foreground_pixels_after": after_count,
        "holes_filled": holes_filled,
        "hole_pixels_filled": hole_pixels,
        "components_removed": components_removed,
        "component_pixels_removed": component_pixels,
        "edge_notch_pixels_filled": edge_pixels,
    }
    child = MaskArtifact(
        artifact_id=f"mask-post-{identity_digest}",
        source_image_asset_id=parent.source_image_asset_id,
        source_digest=parent.source_digest,
        source_width=parent.source_width,
        source_height=parent.source_height,
        mask_asset_id=f"working/masks/postprocessed/{identity_digest}/mask.mask",
        mask_digest=output.digest,
        mask_width=output.width,
        mask_height=output.height,
        transform=transform,
        provenance=parent.provenance,
        prompt=parent.prompt,
        mask_revision=f"maskrev-post-{identity_digest}",
        created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        post_processing_version=(
            f"{MASK_POSTPROCESSING_PIPELINE_ID}/{MASK_POSTPROCESSING_PIPELINE_VERSION}"
        ),
        confidence=parent.confidence,
        parent_mask_revision=parent.mask_revision,
        manual_edit_ancestry=parent.manual_edit_ancestry,
        quality_flags=parent.quality_flags,
        raster=output,
        authority_class=parent.authority_class,
        post_processing_evidence=evidence,
    )
    return MaskPostProcessingResult(parent, child)


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _neighbors(index: int, width: int, height: int) -> tuple[int, ...]:
    x, y = index % width, index // width
    result: list[int] = []
    if x > 0:
        result.append(index - 1)
    if x + 1 < width:
        result.append(index + 1)
    if y > 0:
        result.append(index - width)
    if y + 1 < height:
        result.append(index + width)
    return tuple(result)


def _components(values: list[bool], width: int, height: int, foreground: bool) -> list[list[int]]:
    visited = bytearray(len(values))
    components: list[list[int]] = []
    for start, value in enumerate(values):
        if visited[start] or value is not foreground:
            continue
        visited[start] = 1
        pending = deque([start])
        component: list[int] = []
        while pending:
            index = pending.popleft()
            component.append(index)
            for neighbor in _neighbors(index, width, height):
                if not visited[neighbor] and values[neighbor] is foreground:
                    visited[neighbor] = 1
                    pending.append(neighbor)
        components.append(component)
    return components


def _touches_boundary(component: list[int], width: int, height: int) -> bool:
    return any(
        index % width in (0, width - 1) or index // width in (0, height - 1) for index in component
    )


def _fill_small_holes(
    values: list[bool], width: int, height: int, threshold: int
) -> tuple[int, int]:
    if threshold == 0:
        return 0, 0
    filled = pixels = 0
    for component in _components(values, width, height, foreground=False):
        if len(component) <= threshold and not _touches_boundary(component, width, height):
            for index in component:
                values[index] = True
            filled += 1
            pixels += len(component)
    return filled, pixels


def _fill_single_pixel_notches(values: list[bool], width: int, height: int) -> int:
    if width < 3 or height < 3:
        return 0
    source = tuple(values)
    changed: list[int] = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            index = y * width + x
            if source[index]:
                continue
            if sum(source[neighbor] for neighbor in _neighbors(index, width, height)) == 3:
                changed.append(index)
    for index in changed:
        values[index] = True
    return len(changed)


def _remove_small_components(
    values: list[bool], width: int, height: int, threshold: int
) -> tuple[int, int]:
    if threshold == 0:
        return 0, 0
    removed = pixels = 0
    for component in _components(values, width, height, foreground=True):
        if len(component) <= threshold:
            for index in component:
                values[index] = False
            removed += 1
            pixels += len(component)
    return removed, pixels
