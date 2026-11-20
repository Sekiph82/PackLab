"""Studio-side holder for the active Design Model and its label/export/render chain.

Everything here wires accepted M11-M14 core services together; no geometry, label, CAD or
render logic is reimplemented. All outputs keep ``mm_unverified`` and
``DEFERRED_OWNER_VALIDATION`` semantics from core.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QObject, Signal

from packlab_core.blender_capability import (
    BlenderCapabilityStatus,
    _select_executable,
    discover_blender,
)
from packlab_core.blender_render import render_standard_views
from packlab_core.blender_scene_package import (
    BlenderArtworkBinding,
    BlenderScenePackage,
    ProjectAssetReference,
    create_blender_scene_package,
)
from packlab_core.cad_adapter import cad_shape_precise_bounds
from packlab_core.cad_brep import CadBrepRepresentationRevision, revolve_design_model_to_brep
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfaceAnalysis,
    CadLabelSurfaceCandidate,
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.cad_mesh_export import export_design_model_obj_glb
from packlab_core.cad_preview import CadPreviewMeshRevision, tessellate_brep_preview
from packlab_core.component_material_project import (
    ComponentMaterialProjectEntry,
    create_component_material_project,
)
from packlab_core.component_visual_assignments import (
    create_component_visual_assignment_state,
    create_geometry_material_assignment,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_operations import (
    DesignOperation,
    OperationKind,
    create_revolve_operation,
)
from packlab_core.design_profile import DesignProfile, ProfilePoint, create_design_profile
from packlab_core.design_serialization import (
    MAX_DOCUMENT_BYTES,
    deserialize_design_model,
    serialize_design_model,
)
from packlab_core.label_artwork import (
    LabelArtworkAssetRevision,
    LabelArtworkAssignmentRevision,
    LabelArtworkMappingRevision,
    create_label_artwork_assignment,
    ingest_label_artwork,
)
from packlab_core.label_dieline_svg import LabelDielineSvgExport, export_label_dieline_svg
from packlab_core.label_metric_surface_binding import (
    LabelMetricSurfaceBinding,
    create_label_dieline,
    create_label_dieline_print_intent,
    create_label_metric_surface_binding,
    map_label_artwork_to_metric_surface,
)
from packlab_core.label_zone import LabelZoneBoundary, LabelZoneKind, create_label_zone
from packlab_core.label_zone_placement import (
    LabelZonePlacementRevision,
    create_label_zone_placement_revision,
)
from packlab_core.packaging_sku_library import SkuArtworkPresentationReference
from packlab_core.pbr_visual_parameters import create_pbr_visual_parameter_revision
from packlab_core.reconstruction import ScaleState
from packlab_core.starter_material_catalog import (
    StarterMaterialCatalogRevision,
    StarterMaterialPresetRevision,
    create_starter_packaging_material_catalog,
)

from .engineering_export import DesignModelExportSource, export_dimension_sheet
from .version import current_build_info

DESIGN_DOCUMENT_SUFFIX = ".packlab-design.json"
# Labels are refused on regions curving tighter than this (|k| <= 0.05/mm, radius >= 20 mm).
LABEL_MAXIMUM_ABSOLUTE_CURVATURE_PER_MM = 0.05
_DEFAULT_PROFILE_SAMPLES = 257
_TARGET_NORMAL = {
    LabelZoneKind.FRONT: (0.0, 1.0, 0.0),
    LabelZoneKind.BACK: (0.0, -1.0, 0.0),
    LabelZoneKind.WRAP: (0.0, 1.0, 0.0),
}
_HOST_SURFACE = {
    LabelZoneKind.FRONT: "GeomAbs_Plane",
    LabelZoneKind.BACK: "GeomAbs_Plane",
    LabelZoneKind.WRAP: "GeomAbs_Cylinder",
}
_DEFAULT_BOUNDARY = {
    LabelZoneKind.FRONT: LabelZoneBoundary(0.1, 0.15, 0.9, 0.85),
    LabelZoneKind.BACK: LabelZoneBoundary(0.1, 0.15, 0.9, 0.85),
    LabelZoneKind.WRAP: LabelZoneBoundary(0.0, 0.1, 1.0, 0.9),
}


class DesignWorkbenchError(ValueError):
    """Raised with an owner-readable reason when a Studio design action cannot run."""


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class DesignModelSession:
    """One exact Design Model document plus the BREP/preview derived from it."""

    model: DesignModelRevision
    profile: DesignProfile
    operation: DesignOperation
    representation: CadBrepRepresentationRevision
    preview: CadPreviewMeshRevision
    document_sha256: str
    part_name: str

    @property
    def bounds_mm(self) -> tuple[float, float, float, float, float, float]:
        return cad_shape_precise_bounds(self.representation.shape_handle)

    @property
    def component_id(self) -> str:
        return self.model.features[0].component_id

    @property
    def profile_feature_id(self) -> str:
        return self.operation.parent_feature_ids[0]


@dataclass(frozen=True, slots=True)
class LabelZoneSuggestion:
    kind: LabelZoneKind
    analysis: CadLabelSurfaceAnalysis
    candidate: CadLabelSurfaceCandidate
    boundary: LabelZoneBoundary


@dataclass(slots=True)
class LabelArtwork:
    asset: LabelArtworkAssetRevision
    content: bytes
    mapping: LabelArtworkMappingRevision
    assignment: LabelArtworkAssignmentRevision


@dataclass(slots=True)
class LabelZoneEntry:
    kind: LabelZoneKind
    variant_id: str
    placement: LabelZonePlacementRevision
    analysis: CadLabelSurfaceAnalysis
    metric_binding: LabelMetricSurfaceBinding
    artwork: LabelArtwork | None = None

    @property
    def size_mm(self) -> tuple[float, float]:
        b = self.placement.boundary
        return (
            (b.u_max - b.u_min) * self.metric_binding.host_width_mm_unverified,
            (b.v_max - b.v_min) * self.metric_binding.host_height_mm_unverified,
        )


def _exact_profile_sample_count(profile: DesignProfile) -> int:
    """Samples that land exactly on control points when the profile is piecewise linear.

    A straight profile sampled 257 times would become 256 tiny faces; landing on the control
    points keeps one exact cylinder/cone face per segment, which label binding needs.
    """
    points = profile.points
    start, end = points[0].axial, points[-1].axial
    step = (end - start) / (len(points) - 1)
    uniform = all(
        abs(point.axial - (start + index * step)) <= 1e-9 * max(1.0, abs(end))
        for index, point in enumerate(points)
    )
    linear = all(
        abs(
            profile.evaluate(left.axial + t * (right.axial - left.axial)).radius
            - (left.radius + t * (right.radius - left.radius))
        )
        <= 1e-9
        for left, right in zip(points, points[1:])
        for t in (0.25, 0.5, 0.75)
    )
    if uniform and linear:
        return max(3, len(points))
    return _DEFAULT_PROFILE_SAMPLES


def load_design_model_session(
    source: str | Path | bytes, *, part_name: str = ""
) -> DesignModelSession:
    """Open a canonical Design Model document and derive its BREP + preview."""
    if isinstance(source, bytes):
        data = source
    else:
        path = Path(source)
        if not path.is_file() or path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise DesignWorkbenchError("Design Model file is missing or too large.")
        data = path.read_bytes()
        part_name = part_name or path.name.removesuffix(DESIGN_DOCUMENT_SUFFIX).removesuffix(
            ".json"
        )
    document = deserialize_design_model(data)
    revolves = [item for item in document.operations if item.kind is OperationKind.REVOLVE]
    if len(revolves) != 1:
        raise DesignWorkbenchError(
            "Only single-revolve Design Models (jars, bottles) are supported here."
        )
    operation = revolves[0]
    profile = next(
        (item for item in document.profiles if item.profile_id in operation.input_ids), None
    )
    if profile is None:
        raise DesignWorkbenchError("The Design Model revolve has no profile.")
    model = document.model
    representation = revolve_design_model_to_brep(
        model, profile, operation, profile_sample_count=_exact_profile_sample_count(profile)
    )
    preview = tessellate_brep_preview(model, representation)
    name = re.sub(r"[^A-Za-z0-9 ._-]+", "_", part_name).strip() or "design-model"
    return DesignModelSession(
        model,
        profile,
        operation,
        representation,
        preview,
        hashlib.sha256(data).hexdigest(),
        name[:80],
    )


def nominal_jar_design_document(
    *,
    height_mm: float,
    diameter_mm: float,
    project_id: str = "packlab-nominal-jar",
    actor_id: str = "studio-user",
    created_at_utc: str | None = None,
) -> bytes:
    """User-authored nominal jar (straight revolve) as a canonical Design Model document."""
    if not (math.isfinite(height_mm) and math.isfinite(diameter_mm)):
        raise DesignWorkbenchError("Jar dimensions must be finite.")
    if not (1.0 <= height_mm <= 2000.0 and 1.0 <= diameter_mm <= 2000.0):
        raise DesignWorkbenchError("Jar dimensions must be between 1 and 2000 mm.")
    now = created_at_utc or _utc_now()
    component = "jar-body"
    profile_feature = DesignModelFeatureReference(
        stable_feature_id(component, FeatureKind.BODY, "body-profile"),
        component,
        FeatureKind.BODY,
        "body-profile",
    )
    axis_feature = DesignModelFeatureReference(
        stable_feature_id(component, FeatureKind.BODY, "revolve-axis"),
        component,
        FeatureKind.BODY,
        "revolve-axis",
    )
    reason = f"Nominal jar {height_mm:g} mm tall, {diameter_mm:g} mm diameter."
    root = create_standalone_design_geometry_root(
        project_id=project_id,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id=f"nominal-jar:h{height_mm:g}-d{diameter_mm:g}",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="nominal-jar:unit-mm",
        actor_id=actor_id,
        reason=reason,
        created_at_utc=now,
    )
    model = create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.JAR,
        features=(profile_feature, axis_feature),
        actor_id=actor_id,
        reason=reason,
        created_at_utc=now,
    )
    height_mm, radius = float(height_mm), float(diameter_mm) / 2.0  # ints break profile ids
    profile = create_design_profile(
        (ProfilePoint(0.0, radius), ProfilePoint(height_mm, radius)),
        ScaleState.METRIC_UNVERIFIED,
    )
    operation = create_revolve_operation(
        model,
        profile,
        profile_feature_id=profile_feature.feature_id,
        axis_feature_id=axis_feature.feature_id,
        axis_origin=(0.0, 0.0, 0.0),
        axis_direction=(0.0, 0.0, 1.0),
        angle_degrees=360.0,
    )
    return serialize_design_model(model, profiles=(profile,), operations=(operation,))


def _build_revision() -> str:
    revision = current_build_info().build_revision
    if re.fullmatch(r"[0-9a-f]{40}", revision):
        return revision
    try:  # source checkout: provenance comes from git, never invented
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        completed = None
    value = completed.stdout.strip() if completed is not None else ""
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise DesignWorkbenchError("Render provenance needs the PackLab build revision.")
    return value


def find_blender() -> Path | None:
    """Existing core discovery: PATH, then the standard Blender Foundation folders."""
    capability = discover_blender()
    if capability.status is not BlenderCapabilityStatus.READY:
        return None
    import os
    import shutil
    import sys

    selected = _select_executable(None, shutil.which, sys.platform, os.environ)
    return selected[0] if selected is not None else None


@dataclass(slots=True)
class MockupJob:
    """Prepared scene package; ``run`` only launches Blender so it can leave the UI thread."""

    executable: Path
    root: Path
    package: BlenderScenePackage
    bounds_min: tuple[float, float, float]
    bounds_max: tuple[float, float, float]
    revisions: tuple[tuple[str, str], ...]
    commit: str
    result: dict[str, object] = field(default_factory=dict)

    def run(self) -> dict[str, object]:
        self.result = render_standard_views(
            self.executable,
            self.package,
            self.bounds_min,
            self.bounds_max,
            self.revisions,
            self.root,
            width=640,
            height=640,
            samples=16,
            timeout_seconds=300.0,
            packlab_commit=self.commit,
            packlab_version=current_build_info().studio_version,
        )
        return self.result


class DesignWorkbench(QObject):
    """Active Design Model, its label zones/artwork, material choice and derived outputs."""

    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.session: DesignModelSession | None = None
        self.labels: list[LabelZoneEntry] = []
        self.catalog: StarterMaterialCatalogRevision = create_starter_packaging_material_catalog()
        self.material_id = "material-hdpe-white-visual"

    # ------------------------------------------------------------------ Design Model
    def open_document(
        self, source: str | Path | bytes, *, part_name: str = ""
    ) -> DesignModelSession:
        session = load_design_model_session(source, part_name=part_name)
        self.session = session
        self.labels = []
        self.changed.emit()
        return session

    def require_session(self) -> DesignModelSession:
        if self.session is None:
            raise DesignWorkbenchError("Open a Design Model first.")
        return self.session

    def export_source(self) -> DesignModelExportSource | None:
        session = self.session
        if session is None:
            return None
        return DesignModelExportSource(
            session.model, session.representation, session.preview, session.part_name
        )

    def summary(self) -> str:
        session = self.session
        if session is None:
            return "No Design Model open."
        x0, y0, z0, x1, y1, z1 = session.bounds_mm
        return (
            f"{session.part_name}: {session.model.package_family.value}, "
            f"height {z1 - z0:.1f} mm, width {x1 - x0:.1f} mm, depth {y1 - y0:.1f} mm "
            f"({session.model.coordinate_unit}); revision {session.model.revision_id}; "
            "physical validation DEFERRED_OWNER_VALIDATION."
        )

    # ------------------------------------------------------------------ labels
    def suggest_label_zone(self, kind: LabelZoneKind) -> LabelZoneSuggestion:
        """Pick a curvature-safe host region from the exact CAD label-surface analysis."""
        session = self.require_session()
        # Front/back panels must face +/-Y (within 5 deg); a wrap goes all the way round.
        slope = 90.0 if kind is LabelZoneKind.WRAP else 5.0
        policy = CadLabelSurfacePolicy(
            _TARGET_NORMAL[kind], slope, LABEL_MAXIMUM_ABSOLUTE_CURVATURE_PER_MM
        )
        analysis = analyze_cad_label_surfaces(session.model, session.representation, policy)
        surface = _HOST_SURFACE[kind]
        candidates = [
            item
            for item in analysis.candidates
            if item.surface_type == surface
            and "curvature_threshold_exceeded" not in item.rejection_reasons
            and (
                kind is LabelZoneKind.WRAP or item.advisory_classification == "LABEL_SAFE_CANDIDATE"
            )
        ]
        if not candidates:
            if kind is LabelZoneKind.WRAP:
                raise DesignWorkbenchError(
                    "No curvature-safe cylindrical face for a wrap label on this Design Model."
                )
            raise DesignWorkbenchError(
                f"No flat {kind.value} panel facing {'+Y' if kind is LabelZoneKind.FRONT else '-Y'}"
                " on this Design Model; a round jar or bottle takes a wrap label."
            )
        # Prefer regions away from face trims, then the lowest band (the body, not a lid).
        candidate = min(
            candidates,
            key=lambda item: (len(item.rejection_reasons), round(item.center[2], 6)),
        )
        return LabelZoneSuggestion(kind, analysis, candidate, _DEFAULT_BOUNDARY[kind])

    def add_label_zone(
        self,
        suggestion: LabelZoneSuggestion,
        *,
        boundary: LabelZoneBoundary | None = None,
        variant_id: str | None = None,
        actor_id: str = "studio-user",
    ) -> LabelZoneEntry:
        session = self.require_session()
        if suggestion.analysis.source_design_model_revision_id != session.model.revision_id:
            raise DesignWorkbenchError("The suggestion belongs to another Design Model.")
        chosen = boundary or suggestion.boundary
        zone = create_label_zone(
            session.model,
            session.representation,
            zone_kind=suggestion.kind,
            component_id=session.component_id,
            feature_id=session.profile_feature_id,
            boundary=chosen,
        )
        placement = create_label_zone_placement_revision(
            zone,
            chosen,
            actor_id=actor_id,
            reason=f"Place a {suggestion.kind.value} label zone in Studio.",
            created_at_utc=_utc_now(),
        )
        binding = create_label_metric_surface_binding(
            session.model,
            session.representation,
            placement,
            suggestion.analysis,
            suggestion.candidate.analysis_region_id,
        )
        variant = variant_id or suggestion.kind.value
        if any(item.variant_id == variant for item in self.labels):
            raise DesignWorkbenchError(f"A label variant named {variant!r} already exists.")
        entry = LabelZoneEntry(suggestion.kind, variant, placement, suggestion.analysis, binding)
        self.labels.append(entry)
        self.changed.emit()
        return entry

    def import_artwork(
        self, entry: LabelZoneEntry, source: str | Path | bytes, *, fit_mode: str = "CONTAIN"
    ) -> LabelArtwork:
        content = Path(source).read_bytes() if isinstance(source, (str, Path)) else bytes(source)
        asset = ingest_label_artwork(content)
        mapping = map_label_artwork_to_metric_surface(
            asset, entry.placement, entry.metric_binding, fit_mode=fit_mode
        )
        assignment = create_label_artwork_assignment(
            mapping,
            entry.placement,
            variant_id=entry.variant_id,
            wrap_seam_u_normalized=0.0 if entry.kind is LabelZoneKind.WRAP else None,
            previous=entry.artwork.assignment if entry.artwork is not None else None,
        )
        entry.artwork = LabelArtwork(asset, content, mapping, assignment)
        self.changed.emit()
        return entry.artwork

    def export_dieline_svg(
        self,
        entry: LabelZoneEntry,
        destination: str | Path,
        *,
        safe_margin_mm: float = 2.0,
        bleed_mm: float = 1.5,
    ) -> tuple[Path, LabelDielineSvgExport]:
        dieline = create_label_dieline(entry.metric_binding, entry.placement)
        intent = create_label_dieline_print_intent(
            dieline, safe_margin_mm_unverified=safe_margin_mm, bleed_mm_unverified=bleed_mm
        )
        export = export_label_dieline_svg(intent, entry.placement)
        target = _new_file(Path(destination), f"{self._stem()}-{entry.variant_id}-dieline.svg")
        target.write_bytes(export.svg_bytes)
        target.with_suffix(".json").write_text(
            json.dumps(export.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return target, export

    def sku_artwork_references(
        self, _asset_id: str = "", _asset_revision_id: str = ""
    ) -> tuple[SkuArtworkPresentationReference, ...]:
        """Accepted label artwork assignments of the open Design Model, for SKU creation."""
        references = []
        for entry in self.labels:
            if entry.artwork is None:
                continue
            zone = entry.placement.label_zone
            references.append(
                SkuArtworkPresentationReference(
                    label_zone_id=zone.zone_id,
                    label_zone_design_model_revision_id=zone.source_design_model_revision_id,
                    label_zone_brep_revision_id=zone.source_brep_revision_id,
                    label_zone_brep_geometry_sha256=zone.source_brep_geometry_sha256,
                    artwork_revision_id=entry.artwork.asset.revision_id,
                    artwork_content_sha256=entry.artwork.asset.content_sha256,
                    mapping_revision_id=entry.artwork.mapping.revision_id,
                    assignment_revision_id=entry.artwork.assignment.revision_id,
                    variant_id=entry.variant_id,
                )
            )
        return tuple(references)

    # ------------------------------------------------------------------ materials/render
    @property
    def material(self) -> StarterMaterialPresetRevision:
        return next(
            item for item in self.catalog.entries if item.material.material_id == self.material_id
        )

    def set_material(self, material_id: str) -> None:
        if all(item.material.material_id != material_id for item in self.catalog.entries):
            raise DesignWorkbenchError("Unknown starter material.")
        self.material_id = material_id
        self.changed.emit()

    def prepare_mockup(
        self, destination: str | Path, *, executable: Path | None = None
    ) -> MockupJob:
        """Build the validated Blender scene package; rendering is ``MockupJob.run``."""
        session = self.require_session()
        blender = executable or find_blender()
        if blender is None:
            raise DesignWorkbenchError(
                "Blender 5.x was not found. Install Blender from blender.org (or put blender "
                "on PATH) to render mockups; labels and dielines work without it."
            )
        commit = _build_revision()
        root = _new_directory(Path(destination), f"{self._stem()}-mockup")
        assets = root / "assets"
        assets.mkdir()
        model, brep = session.model, session.representation
        cad_export = export_design_model_obj_glb(
            model, brep, session.preview, assets / "model.obj", assets / "model.glb"
        )
        library = self.catalog.library
        preset = self.material
        material_assignment = create_geometry_material_assignment(
            model, session.component_id, library, preset.material.material_id
        )
        pbr = create_pbr_visual_parameter_revision(
            material_assignment,
            base_color_rgb=preset.material.base_color_rgba[:3],
            roughness_factor=preset.material.roughness_factor,
            transmission_factor=preset.transmission_factor,
            opacity_factor=preset.opacity_factor,
            ior=preset.ior,
        )
        project = create_component_material_project(
            model,
            library,
            (
                ComponentMaterialProjectEntry(
                    session.component_id,
                    create_component_visual_assignment_state(material_assignment),
                ),
            ),
        )
        bindings = []
        for index, entry in enumerate(self.labels):
            if entry.artwork is None:
                continue
            png = _render_png(entry.artwork, entry.size_mm)
            relative = f"assets/label-{index}.png"
            (root / relative).write_bytes(png)
            asset = ingest_label_artwork(png)
            mapping = map_label_artwork_to_metric_surface(
                asset,
                entry.placement,
                entry.metric_binding,
                fit_mode=entry.artwork.mapping.fit_mode,
            )
            assignment = create_label_artwork_assignment(
                mapping,
                entry.placement,
                variant_id=entry.variant_id,
                wrap_seam_u_normalized=0.0 if entry.kind is LabelZoneKind.WRAP else None,
            )
            bindings.append(
                BlenderArtworkBinding(
                    assignment,
                    entry.placement,
                    mapping,
                    asset,
                    ProjectAssetReference(relative, asset.content_sha256, asset.byte_size),
                    entry.analysis,
                    entry.metric_binding,
                )
            )
        glb = (assets / "model.glb").read_bytes()
        package = create_blender_scene_package(
            model,
            cad_export,
            ProjectAssetReference("assets/model.glb", hashlib.sha256(glb).hexdigest(), len(glb)),
            project,
            library,
            pbr_parameters=(pbr,),
            artwork_bindings=tuple(bindings),
            brep_representation=brep,
        )
        (root / "blender_scene_manifest.json").write_bytes(package.manifest_bytes)
        body = cast(dict[str, Any], package.manifest()["body"])
        revisions = tuple(
            sorted(
                (key.removesuffix("_revision_id"), str(value))
                for key, value in cast(dict[str, Any], body["source"]).items()
                if key.endswith("_revision_id")
            )
        )
        x0, y0, z0, x1, y1, z1 = session.bounds_mm
        # Blender scene: metres, CAD +Y appears as -Y (same framing as the PL-0391 mockup).
        return MockupJob(
            blender,
            root,
            package,
            (x0 / 1000.0, -y1 / 1000.0, z0 / 1000.0),
            (x1 / 1000.0, -y0 / 1000.0, z1 / 1000.0),
            revisions,
            commit,
        )

    # ------------------------------------------------------------------ dimension sheet
    def export_dimension_sheet(self, destination: str | Path) -> dict[str, Path]:
        session = self.require_session()
        folder = Path(destination)
        if not folder.is_dir():
            raise DesignWorkbenchError("Choose an existing folder.")
        return export_dimension_sheet(
            session.model,
            session.representation,
            folder,
            stem=self._stem(),
            generated_at_utc=_utc_now(),
        )

    def _stem(self) -> str:
        session = self.require_session()
        return re.sub(r"[^A-Za-z0-9._-]+", "_", session.part_name).strip("._-") or "design-model"


def _new_file(folder: Path, name: str) -> Path:
    if not folder.is_dir():
        raise DesignWorkbenchError("Choose an existing folder.")
    target = folder / name
    if target.exists():
        raise DesignWorkbenchError(f"{name} already exists in that folder; nothing overwritten.")
    return target


def _new_directory(folder: Path, stem: str) -> Path:
    if not folder.is_dir():
        raise DesignWorkbenchError("Choose an existing folder.")
    for index in range(1, 1000):
        target = folder / (stem if index == 1 else f"{stem}-{index}")
        if not target.exists():
            target.mkdir()
            return target
    raise DesignWorkbenchError("Too many mockup folders in that location.")


def _render_png(artwork: LabelArtwork, size_mm: tuple[float, float]) -> bytes:
    """Blender textures need PNG; an SVG is rasterised (render-only, ~8 px/mm, <= 2048 px)."""
    if artwork.asset.media_type == "image/png":
        return artwork.content
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(QByteArray(artwork.content))
    if not renderer.isValid():
        raise DesignWorkbenchError("The SVG artwork could not be rasterised for the mockup.")
    aspect = artwork.asset.width / artwork.asset.height
    width = max(64, min(2048, round(max(size_mm) * 8)))
    height = max(1, round(width / aspect))
    if height > 2048:
        height, width = 2048, max(1, round(2048 * aspect))
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")  # type: ignore[call-overload]
    return bytes(buffer.data().data())


__all__ = [
    "DESIGN_DOCUMENT_SUFFIX",
    "DesignModelSession",
    "DesignWorkbench",
    "DesignWorkbenchError",
    "LabelZoneEntry",
    "LabelZoneSuggestion",
    "MockupJob",
    "find_blender",
    "load_design_model_session",
    "nominal_jar_design_document",
]
