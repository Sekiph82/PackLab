"""Package-family Design Models for the Studio window (PL-0459).

Glue only: geometry, authority and validation stay in accepted core modules
(``tube_family``, ``pouch_family``, ``closure_workflow``, ``mating_references``,
``jerrycan_body_fit``, ``cad_brep``, ``cad_boolean``, ``design_model_binding``). Families come
from one of two explicit parents:

* captured: a revision of the project's selected Scan Master lineage (closure on the selected
  container Design Model, tube bound to the selected Scan Master, jerrycan body fit);
* standalone: an ADR-0005 ``STANDALONE_DESIGN_GEOMETRY`` root from user/preset nominal
  dimensions (``USER_AUTHORED_NOMINAL_DIMENSIONS``), never presented as a measured product.

Everything stays ``mm_unverified`` with ``DEFERRED_OWNER_VALIDATION``; threads, seals, film
deformation and manufacturing fit are recorded as not modelled / not claimed.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from packlab_core.bounding_dimensions import NormalizedMeasurementGeometry
from packlab_core.cad_boolean import (
    PARAMETRIC_HANDLE_OPENING_PREFIX,
    cut_parametric_handle_opening,
)
from packlab_core.cad_brep import (
    CadBrepRepresentationRevision,
    loft_design_model_to_brep,
    revolve_design_model_to_brep,
)
from packlab_core.cad_preview import CadPreviewMeshRevision, tessellate_brep_preview
from packlab_core.cross_section import (
    CrossSection,
    CrossSectionSymmetry,
    SectionPoint,
    create_cross_section,
)
from packlab_core.cross_section_measurement import CrossSectionSelection
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    create_standalone_design_model_revision,
    revise_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometryRoot,
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.design_operations import (
    DesignOperation,
    LoftSectionInput,
    create_loft_operation,
    create_revolve_operation,
)
from packlab_core.design_profile import DesignProfile, ProfilePoint, create_design_profile
from packlab_core.design_serialization import (
    DOCUMENT_CONTRACT,
    _canonical_json,
    deserialize_design_model,
    serialize_design_model,
)
from packlab_core.fitting_strategy import PrincipalAxis, recommend_fitting_strategy
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.jerrycan_body_fit import JerrycanFrontDirection, fit_jerrycan_body
from packlab_core.label_artwork import ingest_label_artwork
from packlab_core.mating_references import (
    MatingReferenceResult,
    create_neck_closure_mating_references,
)
from packlab_core.pouch_family import (
    PouchArtworkAnchor,
    PouchFamilyDimensions,
    PouchFamilyRevision,
    build_pouch_family,
    edit_pouch_family,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision
from packlab_core.tube_family import TubeFamilyDimensions, build_tube_family

from .engineering_export import DesignModelExportSource

STUDIO_REVISION_CONTRACT = "packlab.studio-design-model-revision.v1"
WORKFLOW_CONTRACT = "packlab.studio-package-family.v1"
DEFERRED = "DEFERRED_OWNER_VALIDATION"
UNIT = "mm_unverified"
SECTION_POINTS = 48


class PackageFamilyError(ValueError):
    """Owner-readable refusal from a package-family action."""


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _feature(component: str, kind: FeatureKind, key: str) -> DesignModelFeatureReference:
    return DesignModelFeatureReference(
        stable_feature_id(component, kind, key), component, kind, key
    )


# ------------------------------------------------------------------ families and presets

FAMILIES: dict[str, str] = {
    "closure": "Cap / closure on the selected container",
    "jerrycan": "Jerrycan (body, handle, spout, cap)",
    "trigger_pump": "Trigger / pump bottle",
    "tube": "Tube",
    "pouch": "Sachet / pouch",
}

# Editable key dimensions per family (mm_unverified). Labels are shown in the window.
PARAMETERS: dict[str, tuple[tuple[str, str], ...]] = {
    "closure": (
        ("closure_line", "Closure line height"),
        ("cap_diameter", "Cap outer diameter"),
        ("cap_height", "Cap height"),
        ("neck_finish_diameter", "Neck finish (thread) diameter"),
        ("thread_pitch", "Thread pitch"),
        ("thread_starts", "Thread starts"),
    ),
    "jerrycan": (
        ("width", "Body width"),
        ("depth", "Body depth"),
        ("body_height", "Body height"),
        ("shoulder_height", "Shoulder height"),
        ("handle_height", "Handle bridge height"),
        ("handle_opening_width", "Handle opening width"),
        ("handle_opening_height", "Handle opening height"),
        ("handle_grip_thickness", "Handle grip thickness"),
        ("spout_diameter", "Spout diameter"),
        ("spout_height", "Spout height"),
        ("cap_diameter", "Cap diameter"),
        ("cap_height", "Cap height"),
    ),
    "trigger_pump": (
        ("bottle_diameter", "Bottle diameter"),
        ("body_height", "Body height"),
        ("shoulder_height", "Shoulder height"),
        ("neck_diameter", "Neck diameter"),
        ("neck_height", "Neck height"),
        ("collar_diameter", "Closure collar diameter"),
        ("head_height", "Head height"),
        ("head_length", "Head reach (nozzle)"),
        ("head_width", "Head width"),
        ("dip_tube_diameter", "Dip tube diameter"),
    ),
    "tube": (
        ("body_length", "Body length"),
        ("body_diameter", "Body diameter"),
        ("shoulder_length", "Shoulder length"),
        ("shoulder_diameter", "Shoulder diameter"),
        ("neck_length", "Neck length"),
        ("neck_diameter", "Neck diameter"),
        ("cap_height", "Cap height"),
        ("cap_diameter", "Cap diameter"),
        ("crimp_length", "Crimp length"),
        ("crimp_thickness", "Crimp thickness"),
    ),
    "pouch": (
        ("overall_width", "Overall width"),
        ("overall_height", "Overall height"),
        ("thickness", "Filled thickness"),
        ("top_seal_width", "Top seal"),
        ("bottom_seal_width", "Bottom seal"),
        ("left_seal_width", "Left seal"),
        ("right_seal_width", "Right seal"),
    ),
}

# Nominal starting points typed by PackLab, not measured products (standalone provenance).
PRESETS: dict[str, dict[str, dict[str, float]]] = {
    "closure": {
        "Screw cap sized from the container": {},
        "38 mm screw cap": {"cap_diameter": 38.0, "cap_height": 16.0, "neck_finish_diameter": 37.0},
        "63 mm screw cap": {"cap_diameter": 63.0, "cap_height": 12.0, "neck_finish_diameter": 62.0},
        "70 mm jar lid": {"cap_diameter": 70.0, "cap_height": 10.0, "neck_finish_diameter": 69.0},
    },
    "jerrycan": {
        "5 L jerrycan": {
            "width": 190.0,
            "depth": 125.0,
            "body_height": 215.0,
            "shoulder_height": 35.0,
            "handle_height": 40.0,
            "handle_opening_width": 95.0,
            "handle_opening_height": 26.0,
            "handle_grip_thickness": 14.0,
            "spout_diameter": 42.0,
            "spout_height": 22.0,
            "cap_diameter": 50.0,
            "cap_height": 18.0,
        },
        "10 L jerrycan": {
            "width": 235.0,
            "depth": 155.0,
            "body_height": 265.0,
            "shoulder_height": 40.0,
            "handle_height": 45.0,
            "handle_opening_width": 110.0,
            "handle_opening_height": 30.0,
            "handle_grip_thickness": 15.0,
            "spout_diameter": 45.0,
            "spout_height": 24.0,
            "cap_diameter": 55.0,
            "cap_height": 20.0,
        },
        "20 L jerrycan": {
            "width": 290.0,
            "depth": 190.0,
            "body_height": 330.0,
            "shoulder_height": 45.0,
            "handle_height": 50.0,
            "handle_opening_width": 120.0,
            "handle_opening_height": 32.0,
            "handle_grip_thickness": 16.0,
            "spout_diameter": 55.0,
            "spout_height": 26.0,
            "cap_diameter": 63.0,
            "cap_height": 22.0,
        },
    },
    "trigger_pump": {
        "500 ml trigger sprayer bottle": {
            "bottle_diameter": 68.0,
            "body_height": 165.0,
            "shoulder_height": 30.0,
            "neck_diameter": 28.0,
            "neck_height": 14.0,
            "collar_diameter": 32.0,
            "head_height": 55.0,
            "head_length": 70.0,
            "head_width": 28.0,
            "dip_tube_diameter": 4.5,
        },
        "250 ml lotion pump bottle": {
            "bottle_diameter": 55.0,
            "body_height": 120.0,
            "shoulder_height": 20.0,
            "neck_diameter": 24.0,
            "neck_height": 12.0,
            "collar_diameter": 28.0,
            "head_height": 40.0,
            "head_length": 38.0,
            "head_width": 22.0,
            "dip_tube_diameter": 4.0,
        },
    },
    "tube": {
        "100 ml cosmetic tube": {
            "body_length": 130.0,
            "body_diameter": 38.0,
            "shoulder_length": 8.0,
            "shoulder_diameter": 18.0,
            "neck_length": 8.0,
            "neck_diameter": 12.0,
            "cap_height": 20.0,
            "cap_diameter": 24.0,
            "crimp_length": 10.0,
            "crimp_thickness": 3.0,
        },
        "50 ml tube": {
            "body_length": 100.0,
            "body_diameter": 30.0,
            "shoulder_length": 6.0,
            "shoulder_diameter": 16.0,
            "neck_length": 7.0,
            "neck_diameter": 10.0,
            "cap_height": 16.0,
            "cap_diameter": 20.0,
            "crimp_length": 8.0,
            "crimp_thickness": 3.0,
        },
    },
    "pouch": {
        "Sachet 80 x 120 mm": {
            "overall_width": 80.0,
            "overall_height": 120.0,
            "thickness": 6.0,
            "top_seal_width": 8.0,
            "bottom_seal_width": 8.0,
            "left_seal_width": 5.0,
            "right_seal_width": 5.0,
        },
        "Stand-up pouch 160 x 230 mm": {
            "overall_width": 160.0,
            "overall_height": 230.0,
            "thickness": 30.0,
            "top_seal_width": 10.0,
            "bottom_seal_width": 10.0,
            "left_seal_width": 6.0,
            "right_seal_width": 6.0,
        },
    },
}

# Families that need captured evidence for the captured path, or have no captured path.
STANDALONE_ONLY = frozenset({"trigger_pump", "pouch"})
CAPTURED_ONLY = frozenset({"closure"})

LIMITATIONS: dict[str, tuple[str, ...]] = {
    "closure": (
        "cap modelled as its exterior envelope; internal thread geometry not modelled",
        "thread pitch/starts and neck finish are recorded nominal parameters, not inferred",
        "thread_compatibility_claimed=false; seal_compatibility_claimed=false",
    ),
    "jerrycan": (
        "standalone preset: no captured jerrycan scan; handle opening from nominal parameters",
        "body, spout and cap are separate solids (assembly envelope, no weld/fit claim)",
    ),
    "trigger_pump": (
        "head is a simplified shroud envelope; trigger lever, spring and valve not modelled",
        "dip tube recorded as nominal parameters; core dip-tube/assembly graph needs a captured "
        "Scan Master parent",
    ),
    "tube": ("loft envelope; flexible wall deformation not claimed",),
    "pouch": (
        "visualization-only flexible pack (core): no BREP, STEP/STL not available",
        "film deformation not measured; seal zones flat",
    ),
}


def default_parameters(family: str, preset: str | None = None) -> dict[str, float]:
    presets = PRESETS[family]
    name = preset if preset in presets else next(iter(presets))
    return dict(presets[name])


# ------------------------------------------------------------------ geometry specs


@dataclass(frozen=True)
class _Revolve:
    name: str
    is_cap: bool
    points: tuple[tuple[float, float], ...]  # (axial z, radius), tangents flat
    profile_feature_id: str
    axis_feature_id: str
    axis_origin: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class _Loft:
    name: str
    is_cap: bool
    sections: tuple[tuple[str, float, CrossSection], ...]  # (feature id, z, section)
    handle_feature_id: str | None = None


@dataclass(frozen=True)
class _Spec:
    package_family: PackageFamily
    features: tuple[DesignModelFeatureReference, ...]
    parameters: tuple[DesignModelParameter, ...]
    parts: tuple[_Revolve | _Loft, ...]


def _numbers(prefix: str, values: Mapping[str, float]) -> tuple[DesignModelParameter, ...]:
    return tuple(
        DesignModelParameter(f"{prefix}_{name}", float(value), ParameterType.NUMBER, UNIT)
        for name, value in sorted(values.items())
    )


def _superellipse(
    half_x: float, half_y: float, *, exponent: float = 6.0, center_x: float = 0.0
) -> tuple[SectionPoint, ...]:
    points = []
    for index in range(SECTION_POINTS):
        angle = math.tau * index / SECTION_POINTS
        c, s = math.cos(angle), math.sin(angle)
        points.append(
            SectionPoint(
                center_x + half_x * math.copysign(abs(c) ** (2.0 / exponent), c),
                half_y * math.copysign(abs(s) ** (2.0 / exponent), s),
            )
        )
    return tuple(points)


def _chain(component: str, shapes: tuple[tuple[SectionPoint, ...], ...]) -> list[CrossSection]:
    sections: list[CrossSection] = []
    for points in shapes:
        sections.append(
            create_cross_section(
                component,
                points,
                symmetry=CrossSectionSymmetry.NONE,
                scale_state=ScaleState.METRIC_UNVERIFIED,
                previous_section_id=sections[-1].section_id if sections else None,
            )
        )
    return sections


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageFamilyError(message)


def _positive(values: Mapping[str, float], names: tuple[str, ...]) -> None:
    for name in names:
        value = values.get(name)
        _require(
            isinstance(value, (int, float)) and math.isfinite(value) and 0.0 < value <= 2000.0,
            f"{name.replace('_', ' ')} must be between 0 and 2000 mm",
        )


def _jerrycan_spec(p: Mapping[str, float]) -> _Spec:
    _positive(p, tuple(name for name, _ in PARAMETERS["jerrycan"]))
    w, d = p["width"], p["depth"]
    hb, hs, hh = p["body_height"], p["shoulder_height"], p["handle_height"]
    top = hb + hs + hh
    ow, oh, grip = p["handle_opening_width"], p["handle_opening_height"], p["handle_grip_thickness"]
    spout_r, cap_r = p["spout_diameter"] / 2, p["cap_diameter"] / 2
    margin = 0.08 * w
    spout_x = -w / 2 + margin + cap_r
    _require(cap_r >= spout_r, "cap diameter must be at least the spout diameter")
    _require(grip + oh < hs + hh, "handle opening + grip must fit inside shoulder + handle")
    _require(spout_x + cap_r + 10.0 < w / 2 - margin - ow, "handle opening collides with spout")
    component = "jerrycan-body"
    keys = ("base", "body-top", "shoulder", "handle-root", "handle-top")
    kinds = (
        FeatureKind.BASE,
        FeatureKind.BODY,
        FeatureKind.SHOULDER,
        FeatureKind.BODY,
        FeatureKind.BODY,
    )
    section_features = tuple(
        _feature(component, kind, f"jerrycan:{key}:v1")
        for kind, key in zip(kinds, keys, strict=True)
    )
    shapes = (
        _superellipse(w / 2, d / 2),
        _superellipse(w / 2, d / 2),
        _superellipse(w / 2, 0.42 * d / 2),
        _superellipse(w / 2, 0.30 * d / 2),
        _superellipse(w / 2, 0.30 * d / 2),
    )
    heights = (0.0, hb, hb + hs, hb + hs + 0.5 * hh, top)
    sections = _chain(component, shapes)
    handle = _feature(component, FeatureKind.HANDLE_OPENING, "jerrycan:handle-opening:v1")
    x1 = w / 2 - margin
    x0 = x1 - ow
    z1 = top - grip
    z0 = z1 - oh
    handle_param = DesignModelParameter(
        PARAMETRIC_HANDLE_OPENING_PREFIX + handle.feature_id,
        {
            "body_feature_id": section_features[1].feature_id,
            "profile_xz": [[x0, z0], [x1, z0], [x1, z1], [x0, z1]],
            "source": "USER_AUTHORED_NOMINAL_DIMENSIONS",
            "hidden_extent_inferred": False,
        },
        ParameterType.OBJECT,
    )
    spout_component = "jerrycan-spout"
    spout_profile = _feature(spout_component, FeatureKind.NECK, "jerrycan:spout-profile:v1")
    spout_axis = _feature(spout_component, FeatureKind.NECK, "jerrycan:spout-axis:v1")
    cap_component = "jerrycan-cap"
    cap_profile = _feature(cap_component, FeatureKind.CAP, "jerrycan:cap-profile:v1")
    cap_axis = _feature(cap_component, FeatureKind.CAP, "jerrycan:cap-axis:v1")
    spout_top = top + p["spout_height"]
    cap_top = spout_top + p["cap_height"]
    origin = (spout_x, 0.0, 0.0)
    return _Spec(
        PackageFamily.JERRYCAN,
        (*section_features, handle, spout_profile, spout_axis, cap_profile, cap_axis),
        (*_numbers("jerrycan", p), handle_param),
        (
            _Loft(
                "body",
                False,
                tuple(
                    (feature.feature_id, z, section)
                    for feature, z, section in zip(section_features, heights, sections, strict=True)
                ),
                handle.feature_id,
            ),
            _Revolve(
                "spout",
                False,
                ((top, spout_r), (spout_top, spout_r)),
                spout_profile.feature_id,
                spout_axis.feature_id,
                origin,
            ),
            _Revolve(
                "cap",
                True,
                ((spout_top, cap_r), (cap_top - 2.0, cap_r), (cap_top, cap_r - 2.0)),
                cap_profile.feature_id,
                cap_axis.feature_id,
                origin,
            ),
        ),
    )


def _trigger_spec(p: Mapping[str, float]) -> _Spec:
    _positive(p, tuple(name for name, _ in PARAMETERS["trigger_pump"]))
    r, rn, rc = p["bottle_diameter"] / 2, p["neck_diameter"] / 2, p["collar_diameter"] / 2
    hb, hs, hn = p["body_height"], p["shoulder_height"], p["neck_height"]
    _require(r > rc > rn, "bottle diameter > collar diameter > neck diameter required")
    _require(p["head_length"] >= 2 * rc, "head reach must be at least the collar diameter")
    component = "bottle"
    profile = _feature(component, FeatureKind.BODY, "bottle:profile:v1")
    axis = _feature(component, FeatureKind.BODY, "bottle:axis:v1")
    neck = _feature(component, FeatureKind.NECK, "bottle:neck-finish:v1")
    neck_top = hb + hs + hn
    bottle_points = (
        (0.0, r - 3.0),
        (3.0, r),
        (hb, r),
        (hb + hs, rn),
        (neck_top, rn),
    )
    head_component = "trigger-head"
    keys = ("collar", "collar-top", "shroud", "head-top")
    head_features = tuple(
        _feature(head_component, FeatureKind.TRIGGER_PUMP, f"trigger-pump:{key}:v1") for key in keys
    )
    hh, length, width = p["head_height"], p["head_length"], p["head_width"]
    reach = length / 2 - rc  # forward offset of the shroud centre (+x = nozzle side)
    shapes = (
        _superellipse(rc, rc, exponent=2.0),
        _superellipse(rc, rc, exponent=2.0),
        _superellipse(0.5 * (rc + length / 2), width / 2, exponent=4.0, center_x=0.5 * reach),
        _superellipse(length / 2, width / 2, exponent=4.0, center_x=reach),
    )
    heights = (neck_top, neck_top + 0.3 * hh, neck_top + 0.7 * hh, neck_top + hh)
    sections = _chain(head_component, shapes)
    dip_tube = DesignModelParameter(
        "trigger_pump_dip_tube_nominal",
        {
            "length": hb + hs - 5.0,
            "diameter": p["dip_tube_diameter"],
            "coordinate_unit": UNIT,
            "core_dip_tube_component": "not_created_requires_captured_scan_master_parent",
        },
        ParameterType.OBJECT,
    )
    return _Spec(
        PackageFamily.BOTTLE,
        (profile, axis, neck, *head_features),
        (*_numbers("trigger_pump", p), dip_tube),
        (
            _Revolve("bottle", False, bottle_points, profile.feature_id, axis.feature_id),
            _Loft(
                "head",
                True,
                tuple(
                    (feature.feature_id, z, section)
                    for feature, z, section in zip(head_features, heights, sections, strict=True)
                ),
            ),
        ),
    )


def _tube_dimensions(p: Mapping[str, float]) -> TubeFamilyDimensions:
    _positive(p, tuple(name for name, _ in PARAMETERS["tube"]))
    try:
        return TubeFamilyDimensions(**{name: float(p[name]) for name, _ in PARAMETERS["tube"]})
    except ValueError as error:
        raise PackageFamilyError(f"tube dimensions refused by core: {error}") from error


def _tube_spec(p: Mapping[str, float], project_id: str) -> _Spec:
    # build_tube_family owns features, parameters and sections; its own throwaway model is
    # re-parented below (create under the real parent or revise the previous revision).
    root = _root(
        project_id, "tube", "tube-sections", "Tube section geometry.", "1970-01-01T00:00:00Z"
    )
    built = build_tube_family(
        root,
        _tube_dimensions(p),
        component_id="tube",
        actor_id="studio",
        reason="Tube family sections.",
        created_at_utc="1970-01-01T00:00:00Z",
    )
    positions = built.operation.section_positions
    return _Spec(
        PackageFamily.TUBE,
        built.model.features,
        built.model.parameters,
        (
            _Loft(
                "tube",
                False,
                tuple(
                    (feature_id, z, section)
                    for feature_id, z, section in zip(
                        built.operation.parent_feature_ids, positions, built.sections, strict=True
                    )
                ),
            ),
        ),
    )


def _closure_spec(p: Mapping[str, Any], container: DesignModelRevision) -> _Spec:
    """Container revolve clipped at the closure line + a CAP exterior envelope above it."""
    _positive(
        p, ("closure_line", "cap_diameter", "cap_height", "neck_finish_diameter", "thread_pitch")
    )
    starts = p.get("thread_starts")
    _require(
        isinstance(starts, (int, float)) and float(starts).is_integer() and 1 <= starts <= 8,
        "thread starts must be a whole number from 1 to 8",
    )
    container_points = tuple((float(z), float(r)) for z, r in p["container_profile"])
    profile_feature, axis_feature = p["container_features"]
    line = float(p["closure_line"])
    _require(
        container_points[0][0] + 1.0 < line < container_points[-1][0],
        "closure line must lie between the container base and its top",
    )
    clipped = _clip_profile(container_points, line)
    cap = _feature("closure", FeatureKind.CAP, "closure:screw-cap:v1")
    cap_r = float(p["cap_diameter"]) / 2
    top = line + float(p["cap_height"])
    chamfer = min(1.0, 0.1 * float(p["cap_height"]), 0.1 * cap_r)
    cap_parameter = DesignModelParameter(
        "closure_screw_cap",
        {
            "feature_id": cap.feature_id,
            "component_id": cap.component_id,
            "closure_line": line,
            "cap_diameter": float(p["cap_diameter"]),
            "cap_height": float(p["cap_height"]),
            "neck_finish_diameter": float(p["neck_finish_diameter"]),
            "thread_pitch": float(p["thread_pitch"]),
            "thread_starts": int(float(starts or 0)),
            "neck_finish_designation": "UNSPECIFIED_OWNER_TO_CONFIRM",
            "coordinate_unit": UNIT,
            "internal_thread_geometry_modelled": False,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
        },
        ParameterType.OBJECT,
    )
    caps = {item.feature_id for item in container.features if item.feature_kind is FeatureKind.CAP}
    features = tuple(item for item in container.features if item.feature_id not in caps)
    # A new cap supersedes every earlier closure parameter (cap values, mating references,
    # replacement state): drop parameters that reference a removed CAP feature.
    parameters = tuple(
        item
        for item in container.parameters
        if item.parameter_id != "closure_screw_cap"
        and not any(cap_id in json.dumps(item.as_dict()["value"]) for cap_id in caps)
    )
    return _Spec(
        container.package_family,
        (*features, cap),
        (*parameters, cap_parameter),
        (
            _Revolve("container", False, clipped, profile_feature, axis_feature),
            _Revolve(
                "cap",
                True,
                ((line, cap_r), (top - chamfer, cap_r), (top, cap_r - chamfer)),
                cap.feature_id,
                axis_feature,
            ),
        ),
    )


def _clip_profile(
    points: tuple[tuple[float, float], ...], line: float
) -> tuple[tuple[float, float], ...]:
    kept = [point for point in points if point[0] < line - 1e-6]
    if len(kept) == len(points):
        return points
    left = kept[-1]
    right = next(point for point in points if point[0] >= line - 1e-6)
    t = (line - left[0]) / (right[0] - left[0])
    kept.append((line, left[1] + t * (right[1] - left[1])))
    return tuple(kept)


# ------------------------------------------------------------------ realized design


@dataclass(frozen=True)
class FamilyPart:
    name: str
    is_cap: bool
    operation: DesignOperation
    representation: CadBrepRepresentationRevision
    preview: CadPreviewMeshRevision


@dataclass(frozen=True)
class FamilyDesign:
    family: str
    preset: str
    parameters: dict[str, Any]
    model: DesignModelRevision
    parts: tuple[FamilyPart, ...]
    design_document: bytes
    history: tuple[str, ...]
    proxy_mesh: TriangleMeshData | None = None  # pouch: core preview proxy (no BREP)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def provenance(self) -> str:
        return self.model.parent_kind.value

    def part(self, name: str) -> FamilyPart | None:
        return next((item for item in self.parts if item.name == name), None)

    def export_source(self, name: str) -> DesignModelExportSource | None:
        part = self.part(name)
        if part is None:
            return None
        return DesignModelExportSource(
            self.model,
            part.representation,
            part.preview,
            f"{self.family}-{name}-{self.model.revision_id.split(':')[-1][:8]}",
        )

    def bounds(self) -> tuple[float, float, float, float, float, float]:
        if self.parts:
            boxes = [item.preview.preview_bounds for item in self.parts]
            return (
                min(b[0] for b in boxes),
                max(b[1] for b in boxes),
                min(b[2] for b in boxes),
                max(b[3] for b in boxes),
                min(b[4] for b in boxes),
                max(b[5] for b in boxes),
            )
        assert self.proxy_mesh is not None
        xs, ys, zs = zip(*self.proxy_mesh.vertices, strict=True)
        return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

    def overall_dimensions(self) -> dict[str, float]:
        x0, x1, y0, y1, z0, z1 = self.bounds()
        return {
            "height": round(z1 - z0, 3),
            "width": round(x1 - x0, 3),
            "depth": round(y1 - y0, 3),
            "diameter": round(max(x1 - x0, y1 - y0), 3),
        }

    def as_dict(self) -> dict[str, object]:
        """Studio revision document persisted through ProjectManager (contract v1)."""
        parameters = {
            key: value
            for key, value in self.parameters.items()
            if key not in {"container_profile", "container_features"}
        }
        workflow: dict[str, object] = {
            "contract": WORKFLOW_CONTRACT,
            "family": self.family,
            "family_label": FAMILIES[self.family],
            "preset": self.preset,
            "parameters_mm_unverified": parameters,
            "parent_kind": self.provenance,
            "parts": [
                {
                    "name": item.name,
                    "operation_id": item.operation.operation_id,
                    "brep_revision_id": item.representation.revision_id,
                    "closure_component": item.is_cap,
                }
                for item in self.parts
            ],
            "limitations": list(LIMITATIONS[self.family]),
            **self.extra,
        }
        if "container_profile" in self.parameters:
            workflow["container_profile"] = [
                list(item) for item in self.parameters["container_profile"]
            ]
            workflow["container_features"] = list(self.parameters["container_features"])
        return {
            "contract": STUDIO_REVISION_CONTRACT,
            "design_model_revision_id": self.model.revision_id,
            "revision_history": list(self.history),
            "overall_dimensions_mm_unverified": self.overall_dimensions(),
            "model": self.model.as_dict(),
            "design_document": self.design_document.decode("utf-8"),
            "package_family_workflow": workflow,
            "scan_master_replaced": False,
            "physical_accuracy_validation_status": DEFERRED,
            "mold_use_authorized": False,
        }


def _root(
    project_id: str, family: str, provenance: str, reason: str, created: str
) -> StandaloneDesignGeometryRoot:
    return create_standalone_design_geometry_root(
        project_id=project_id,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id=f"packlab-studio-family:{family}:{provenance}"[:200],
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="packlab-studio-family:nominal-mm",
        actor_id="packlab-studio",
        reason=reason,
        created_at_utc=created,
    )


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")[:60] or "custom"


def _realize(
    family: str,
    preset: str,
    parameters: dict[str, Any],
    spec: _Spec,
    model: DesignModelRevision,
    history: tuple[str, ...],
    extra: dict[str, Any] | None = None,
) -> FamilyDesign:
    """Derive one BREP per part from core operations bound to ``model``."""
    profiles: list[DesignProfile] = []
    sections: list[CrossSection] = []
    parts: list[FamilyPart] = []
    try:
        for part in spec.parts:
            if isinstance(part, _Revolve):
                profile = create_design_profile(
                    tuple(ProfilePoint(z, r, 0.0) for z, r in part.points), model.scale_state
                )
                operation = create_revolve_operation(
                    model,
                    profile,
                    profile_feature_id=part.profile_feature_id,
                    axis_feature_id=part.axis_feature_id,
                    axis_origin=part.axis_origin,
                )
                representation = revolve_design_model_to_brep(model, profile, operation)
                profiles.append(profile)
            else:
                inputs = tuple(
                    LoftSectionInput(feature_id, section, z)
                    for feature_id, z, section in part.sections
                )
                operation = create_loft_operation(model, inputs)
                representation = loft_design_model_to_brep(model, inputs, operation, ruled=True)
                sections.extend(section for _f, _z, section in part.sections)
                if part.handle_feature_id is not None:
                    cut = cut_parametric_handle_opening(
                        model, representation, part.handle_feature_id
                    )
                    if cut.representation is None:
                        raise PackageFamilyError(
                            "handle opening cut failed: " + ", ".join(cut.failure_diagnostics)
                        )
                    representation = cut.representation
            parts.append(
                FamilyPart(
                    part.name,
                    part.is_cap,
                    operation,
                    representation,
                    tessellate_brep_preview(model, representation),
                )
            )
        document = serialize_design_model(
            model,
            profiles=tuple(profiles),
            cross_sections=tuple(sections),
            operations=tuple(item.operation for item in parts),
        )
    except PackageFamilyError:
        raise
    except ValueError as error:
        raise PackageFamilyError(f"core refused the {family} geometry: {error}") from error
    return FamilyDesign(
        family, preset, parameters, model, tuple(parts), document, history, None, extra or {}
    )


def _spec_for(
    family: str,
    parameters: Mapping[str, Any],
    *,
    project_id: str,
    container: DesignModelRevision | None,
) -> _Spec:
    if family == "jerrycan":
        return _jerrycan_spec(parameters)
    if family == "trigger_pump":
        return _trigger_spec(parameters)
    if family == "tube":
        return _tube_spec(parameters, project_id)
    if family == "closure":
        if container is None:
            raise PackageFamilyError("select a container Design Model first")
        return _closure_spec(parameters, container)
    raise PackageFamilyError(f"unsupported family {family}")


def create_standalone(
    family: str, parameters: Mapping[str, Any], *, project_id: str, preset: str, actor_id: str
) -> FamilyDesign:
    """New family Design Model under an ADR-0005 standalone root (no scan evidence)."""
    if family in CAPTURED_ONLY:
        raise PackageFamilyError("a closure needs the selected container; use the captured path")
    created = _now()
    values = {key: float(value) for key, value in parameters.items()}
    provenance = f"preset:{_slug(preset)}" if preset else "user-parameters"
    reason = f"Studio {FAMILIES[family]} from nominal parameters ({preset or 'custom'})."
    root = _root(project_id, family, provenance, reason, created)
    if family == "pouch":
        return _pouch(root, values, preset, actor_id, created, None, None)
    spec = _spec_for(family, values, project_id=project_id, container=None)
    model = create_standalone_design_model_revision(
        root,
        package_family=spec.package_family,
        parameters=spec.parameters,
        features=spec.features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created,
    )
    return _realize(family, preset, values, spec, model, (model.revision_id,))


def create_tube_on_scan_master(
    scan_master: ScanMasterRevision, parameters: Mapping[str, float], *, preset: str, actor_id: str
) -> FamilyDesign:
    """Tube Design Model bound to the selected Scan Master (captured lineage)."""
    created = _now()
    values = {key: float(value) for key, value in parameters.items()}
    try:
        binding = bind_design_model_parent(
            scan_master,
            actor_id=actor_id,
            reason="Tube family on the selected Scan Master.",
            created_at_utc=created,
        )
    except ValueError as error:
        raise PackageFamilyError(f"Scan Master cannot parent a Design Model: {error}") from error
    spec = _tube_spec(values, scan_master.project_id)
    model = create_design_model_revision(
        binding,
        package_family=spec.package_family,
        parameters=spec.parameters,
        features=spec.features,
        actor_id=actor_id,
        reason=f"Tube family ({preset or 'custom'}) bound to the selected Scan Master.",
        created_at_utc=created,
    )
    return _realize("tube", preset, values, spec, model, (model.revision_id,))


def fit_jerrycan_on_scan_master(
    scan_master: ScanMasterRevision, *, section_count: int = 5, actor_id: str
) -> FamilyDesign:
    """Core jerrycan stacked-section body fit (``fit_jerrycan_body``) on the Scan Master."""
    created = _now()
    try:
        strategy = recommend_fitting_strategy(
            scan_master,
            expected_scan_master_revision_id=scan_master.revision_id,
            actor_id=actor_id,
            reason="Assess the Scan Master for a jerrycan section loft.",
            created_at_utc=created,
            upright_axis=PrincipalAxis.Z,
        )
        zs = [vertex[2] for vertex in scan_master.mesh.vertices]
        low, high = min(zs), max(zs)
        heights = tuple(
            low + (high - low) * (0.08 + 0.84 * index / (section_count - 1))
            for index in range(section_count)
        )
        fit = fit_jerrycan_body(
            scan_master,
            strategy,
            expected_scan_master_revision_id=scan_master.revision_id,
            expected_strategy_recommendation_id=strategy.recommendation_id,
            section_heights=heights,
            component_id="jerrycan-body",
            symmetry=CrossSectionSymmetry.BOTH,
            front_direction=JerrycanFrontDirection.POSITIVE_Y,
            actor_id=actor_id,
            reason="Fit a jerrycan body to the selected Scan Master.",
            created_at_utc=created,
        )
    except ValueError as error:
        raise PackageFamilyError(f"core jerrycan body fit refused: {error}") from error
    if fit.review_required:
        raise PackageFamilyError(
            f"core jerrycan body fit needs review ({fit.status.value}); recapture or use a preset"
        )
    inputs = tuple(
        LoftSectionInput(feature_id, section, z)
        for feature_id, z, section in zip(
            fit.operation.parent_feature_ids, fit.section_heights, fit.sections, strict=False
        )
    )
    try:
        representation = loft_design_model_to_brep(fit.model, inputs, fit.operation, ruled=True)
        preview = tessellate_brep_preview(fit.model, representation)
        document = serialize_design_model(
            fit.model, cross_sections=fit.sections, operations=(fit.operation,)
        )
    except ValueError as error:
        raise PackageFamilyError(f"core refused the jerrycan BREP: {error}") from error
    part = FamilyPart("body", False, fit.operation, representation, preview)
    return FamilyDesign(
        "jerrycan",
        "fitted to the selected Scan Master",
        {"section_count": float(section_count)},
        fit.model,
        (part,),
        document,
        (fit.model.revision_id,),
        None,
        {
            "jerrycan_body_fit": {
                "status": fit.status.value,
                "section_heights": list(fit.section_heights),
            }
        },
    )


def _pouch(
    root: StandaloneDesignGeometryRoot,
    values: dict[str, float],
    preset: str,
    actor_id: str,
    created: str,
    previous: PouchFamilyRevision | None,
    artwork: dict[str, Any] | None,
) -> FamilyDesign:
    _positive(values, tuple(name for name, _ in PARAMETERS["pouch"]))
    try:
        dimensions = PouchFamilyDimensions(
            **{name: values[name] for name, _ in PARAMETERS["pouch"]}
        )
        if previous is None:
            revision = build_pouch_family(
                root,
                dimensions,
                component_id="pouch",
                actor_id=actor_id,
                reason=f"Studio sachet/pouch from nominal dimensions ({preset or 'custom'}).",
                created_at_utc=created,
                front_bulge=0.25 * dimensions.thickness,
                back_bulge=0.25 * dimensions.thickness,
            )
        else:
            revision = edit_pouch_family(
                previous,
                dimensions=dimensions,
                front_bulge=0.25 * dimensions.thickness,
                back_bulge=0.25 * dimensions.thickness,
                actor_id=actor_id,
                reason="Studio edit of the sachet/pouch overall dimensions.",
                created_at_utc=created,
            )
        document = serialize_design_model(revision.model)
    except ValueError as error:
        raise PackageFamilyError(f"core refused the pouch: {error}") from error
    extra: dict[str, Any] = {"pouch_family": revision.as_dict()["artwork_surfaces"]}
    if artwork:
        extra["artwork"] = artwork
    design = FamilyDesign(
        "pouch",
        preset,
        values,
        revision.model,
        (),
        document,
        (revision.model.revision_id,),
        revision.preview.mesh,
        extra,
    )
    _POUCH_REVISIONS[revision.model.revision_id] = revision
    return design


# ponytail: keyed cache of the core pouch revisions (edit_pouch_family needs the object);
# bounded by the number of pouches edited in one session.
_POUCH_REVISIONS: dict[str, PouchFamilyRevision] = {}


def attach_pouch_artwork(design: FamilyDesign, artwork_path: str, *, actor_id: str) -> FamilyDesign:
    """Validate SVG/PNG artwork (core ``ingest_label_artwork``) and pin it to the front panel."""
    if design.family != "pouch":
        raise PackageFamilyError("artwork placement here is for sachets/pouches")
    try:
        asset = ingest_label_artwork(artwork_path)
    except ValueError as error:
        raise PackageFamilyError(f"artwork refused by core: {error}") from error
    surfaces = design.extra.get("pouch_family", {})
    front = surfaces.get("front_feature_id")
    anchor = PouchArtworkAnchor("front-artwork-centre", str(front), 0.5, 0.5)
    record = {
        "asset": asset.as_dict(),
        "surface_feature_id": front,
        "anchor": anchor.as_dict(),
        "artwork_bytes_stored": False,
    }
    previous = _POUCH_REVISIONS.get(design.model.revision_id)
    if previous is None:
        raise PackageFamilyError("pouch revision is not open in this session")
    root = design.model.standalone_root
    assert root is not None
    return _pouch(root, dict(design.parameters), design.preset, actor_id, _now(), previous, record)


def edit(
    design: FamilyDesign,
    parameters: Mapping[str, Any],
    *,
    actor_id: str,
    container: DesignModelRevision | None = None,
) -> FamilyDesign:
    """New revision chained to ``design.model`` with the edited key dimensions."""
    if design.family == "jerrycan" and design.part("spout") is None:
        raise PackageFamilyError("a fitted jerrycan body is edited by refitting the Scan Master")
    values: dict[str, Any] = dict(design.parameters)
    values.update({key: float(value) for key, value in parameters.items()})
    created = _now()
    if design.family == "pouch":
        previous = _POUCH_REVISIONS.get(design.model.revision_id)
        if previous is None:
            raise PackageFamilyError("pouch revision is not open in this session")
        root = design.model.standalone_root
        assert root is not None
        return _pouch(
            root, values, design.preset, actor_id, created, previous, design.extra.get("artwork")
        )
    spec = _spec_for(
        design.family,
        values,
        project_id=design.model.project_id,
        container=container or design.model,
    )
    try:
        model = revise_design_model_revision(
            design.model,
            parameters=spec.parameters,
            features=spec.features,
            actor_id=actor_id,
            reason=f"Studio edit of the {FAMILIES[design.family]} key dimensions.",
            created_at_utc=created,
        )
    except ValueError as error:
        raise PackageFamilyError(f"core refused the edit: {error}") from error
    return _realize(
        design.family,
        design.preset,
        values,
        spec,
        model,
        (*design.history, model.revision_id),
        design.extra,
    )


# ------------------------------------------------------------------ closure on a container


def model_from_dict(model_dict: Mapping[str, Any]) -> DesignModelRevision:
    """Strictly re-validate a persisted model dict through the core document parser."""
    body = {
        "contract": DOCUMENT_CONTRACT,
        "model": dict(model_dict),
        "profiles": [],
        "cross_sections": [],
        "operations": [],
    }
    envelope = {"body": body, "content_sha256": hashlib.sha256(_canonical_json(body)).hexdigest()}
    try:
        return deserialize_design_model(_canonical_json(envelope)).model
    except ValueError as error:
        raise PackageFamilyError(f"container Design Model is unreadable: {error}") from error


def container_context(document: Mapping[str, Any]) -> tuple[DesignModelRevision, dict[str, Any]]:
    """Container model + revolve profile from a Measure & Design (or closure) document."""
    workflow = document.get("package_family_workflow")
    if isinstance(workflow, Mapping) and workflow.get("family") == "closure":
        model = model_from_dict(document["model"])
        profile = [tuple(item) for item in workflow["container_profile"]]
        features = tuple(workflow["container_features"])
        return model, {"container_profile": profile, "container_features": features}
    if isinstance(workflow, Mapping):
        raise PackageFamilyError("the selected Design Model is not a revolved container")
    try:
        fit = document["revolved_fit"]
        dims = document["overall_dimensions_mm_unverified"]
        fitted = document["fitted_from_scan"]
        radial = float(dims["diameter"]) / float(fitted["diameter"])
        axial = float(dims["height"]) / float(fitted["height"])
        points = tuple(
            (float(item["axial"]) * axial, float(item["radius"]) * radial)
            for item in fit["profile"]["control_points"]
        )
        features = tuple(fit["operation"]["parent_feature_ids"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise PackageFamilyError(
            "the selected Design Model has no revolved container profile (fit one in Measure & "
            "Design first)"
        ) from error
    model = model_from_dict(document["model"])
    if model.revision_id != document.get("design_model_revision_id"):
        raise PackageFamilyError("container Design Model record is inconsistent")
    return model, {"container_profile": points, "container_features": features}


def closure_defaults(context: Mapping[str, Any], preset: str) -> dict[str, Any]:
    points = context["container_profile"]
    z0, z1 = points[0][0], points[-1][0]
    line = z0 + 0.85 * (z1 - z0)
    top_radii = [r for z, r in points if z >= line] or [points[-1][1]]
    diameter = 2 * max(top_radii)
    values: dict[str, Any] = {
        "closure_line": round(line, 2),
        "cap_diameter": round(diameter, 2),
        "cap_height": round(max(z1 - line, 4.0), 2),
        "neck_finish_diameter": round(diameter - 2.0, 2),
        "thread_pitch": 3.0,
        "thread_starts": 1.0,
    }
    values.update(PRESETS["closure"].get(preset, {}))
    return {**values, **context}


def create_closure(
    container_document: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    preset: str,
    actor_id: str,
) -> FamilyDesign:
    """Screw cap on the selected container: a revision of the container Design Model."""
    container, context = container_context(container_document)
    if container.parent_kind.value != "CAPTURED_SCAN_MASTER":
        raise PackageFamilyError("closures here are added to a Scan Master-fitted container")
    values: dict[str, Any] = {**dict(parameters), **context}
    spec = _closure_spec(values, container)
    try:
        model = revise_design_model_revision(
            container,
            parameters=spec.parameters,
            features=spec.features,
            actor_id=actor_id,
            reason=f"Add screw cap ({preset or 'custom'}) above the closure line "
            f"{float(values['closure_line']):.2f} mm_unverified.",
            created_at_utc=_now(),
        )
    except ValueError as error:
        raise PackageFamilyError(f"core refused the closure revision: {error}") from error
    history = tuple(container_document.get("revision_history", ()) or (container.revision_id,))
    design = _realize(
        "closure",
        preset,
        values,
        spec,
        model,
        (*history, model.revision_id),
        {"assembly": _assembly(container.revision_id, values)},
    )
    return design


def _assembly(container_revision_id: str, values: Mapping[str, Any]) -> dict[str, object]:
    return {
        "contract": "packlab.studio-container-closure-assembly.v1",
        "container_source_revision_id": container_revision_id,
        "placement": "coaxial on the container axis; cap from the closure line upward",
        "closure_line_mm_unverified": float(values["closure_line"]),
        "thread_compatibility_claimed": False,
        "seal_compatibility_claimed": False,
        "interference_checked": False,
    }


def _dense_heights(zs: list[float], low: float, high: float, band: float) -> tuple[float, ...]:
    """Centres of the two most populated slabs (width 2*band) between low and high."""
    edges = [low + 2 * band * index for index in range(int((high - low) / (2 * band)) + 1)]
    counts = [(sum(1 for z in zs if left <= z < left + 2 * band), left + band) for left in edges]
    best = sorted(sorted(counts, reverse=True)[:2], key=lambda item: item[1])
    return tuple(centre for _count, centre in best)


def _ring_selections(
    geometry: NormalizedMeasurementGeometry, heights: tuple[float, ...], label: str, band: float
) -> tuple[CrossSectionSelection, ...]:
    selections = []
    for height in heights:
        indices = tuple(
            index for index, point in enumerate(geometry.points) if abs(point[2] - height) <= band
        )[:4096]
        selections.append(
            CrossSectionSelection(
                f"{label}-z{height:.3f}",
                geometry.source_geometry_id,
                geometry.normalized_geometry_revision,
                indices,
                (0.0, 0.0, height),
                (0.0, 0.0, 1.0),
                band,
            )
        )
    return tuple(selections)


def closure_mating_references(
    scan_master: ScanMasterRevision,
    model: DesignModelRevision,
    neck_feature_id: str,
    closure_feature_id: str,
    closure_line: float,
    *,
    actor_id: str,
) -> MatingReferenceResult:
    """Neck/closure reference planes from Scan Master rings around the closure line (core)."""
    manifest = scan_master.manifest
    try:
        geometry = NormalizedMeasurementGeometry(
            f"studio-closure-sections:{scan_master.revision_id}",
            str(manifest.get("parent_object_geometry_revision_id")),
            tuple(tuple(map(float, vertex)) for vertex in scan_master.mesh.vertices),  # type: ignore[misc]
            ScaleState(str(manifest.get("scale_state"))),
            "mm_unverified"
            if manifest.get("scale_state") == "metric-unverified"
            else "reconstruction_units",
            manifest.get("scale_provenance_id")
            if manifest.get("scale_state") == "metric-unverified"
            else None,  # type: ignore[arg-type]
            1e-6 if manifest.get("scale_state") == "metric-unverified" else None,
            "mm_per_reconstruction_unit"
            if manifest.get("scale_state") == "metric-unverified"
            else None,
        )
        band = 0.25  # core policy: planarity tolerance <= maximum radial residual (0.25)
        zs = [point[2] for point in geometry.points]
        neck = _ring_selections(
            geometry, _dense_heights(zs, closure_line - 6.0, closure_line - 0.5, band), "neck", band
        )
        closure = _ring_selections(
            geometry,
            _dense_heights(zs, closure_line + 0.5, closure_line + 6.0, band),
            "closure",
            band,
        )
        return create_neck_closure_mating_references(
            scan_master,
            geometry,
            model,
            neck_feature_id,
            closure_feature_id,
            neck,
            closure,
            expected_scan_master_revision_id=scan_master.revision_id,
            expected_model_revision_id=model.revision_id,
            actor_id=actor_id,
            reason="Neck/closure reference planes from Scan Master rings at the closure line.",
            created_at_utc=_now(),
        )
    except ValueError as error:
        raise PackageFamilyError(f"core mating references refused: {error}") from error


def replacement_base(
    design: FamilyDesign, parameters: Mapping[str, Any], *, actor_id: str
) -> tuple[DesignModelRevision, str, str]:
    """Current closure model + an alternate CAP feature (the replacement candidate)."""
    current = design.model
    count = sum(1 for item in current.features if item.feature_kind is FeatureKind.CAP)
    key = f"closure:screw-cap-alternate-{len(design.history)}:v1"
    cap = _feature("closure", FeatureKind.CAP, key)
    _require(count >= 1, "the current model has no closure to replace")
    values = {**design.parameters, **{k: float(v) for k, v in parameters.items()}}
    parameter_id = f"closure_alternate_{len(design.history)}"
    alternate = DesignModelParameter(
        parameter_id,
        {
            "feature_id": cap.feature_id,
            "component_id": cap.component_id,
            "cap_diameter": float(values["cap_diameter"]),
            "cap_height": float(values["cap_height"]),
            "neck_finish_diameter": float(values["neck_finish_diameter"]),
            "thread_pitch": float(values["thread_pitch"]),
            "thread_starts": int(values["thread_starts"]),
            "closure_line": float(values["closure_line"]),
            "coordinate_unit": UNIT,
            "thread_compatibility_claimed": False,
            "seal_compatibility_claimed": False,
        },
        ParameterType.OBJECT,
    )
    try:
        model = revise_design_model_revision(
            current,
            parameters=(*current.parameters, alternate),
            features=(*current.features, cap),
            actor_id=actor_id,
            reason="Prepare an alternate closure component candidate.",
            created_at_utc=_now(),
        )
    except ValueError as error:
        raise PackageFamilyError(f"core refused the alternate closure: {error}") from error
    return model, cap.feature_id, parameter_id


def current_cap(design: FamilyDesign) -> tuple[str, str, dict[str, Any]]:
    """(feature id, parameter id, values) of the active CAP feature in a closure model."""
    caps = {
        item.feature_id for item in design.model.features if item.feature_kind is FeatureKind.CAP
    }
    for parameter in design.model.parameters:
        value = parameter.as_dict()["value"]
        if isinstance(value, dict) and value.get("feature_id") in caps:
            return str(value["feature_id"]), parameter.parameter_id, value
    raise PackageFamilyError("closure model has no active cap parameters")


def adopt_model(
    design: FamilyDesign, model: DesignModelRevision, *, extra: Mapping[str, Any] | None = None
) -> FamilyDesign:
    """Re-derive closure geometry for a core-produced revision (replace / undo / redo)."""
    _feature_id, _parameter_id, values = current_cap(
        FamilyDesign(
            design.family, design.preset, design.parameters, model, (), b"", design.history
        )
    )
    parameters = {
        **design.parameters,
        **{
            key: float(values[key])
            for key in (
                "closure_line",
                "cap_diameter",
                "cap_height",
                "neck_finish_diameter",
                "thread_pitch",
                "thread_starts",
            )
            if key in values
        },
    }
    cap_feature = next(item for item in model.features if item.feature_id == _feature_id)
    spec = _closure_spec(parameters, model)
    # Keep the model's own CAP feature (core chose it); geometry follows its parameters.
    parts = tuple(
        part
        if part.name != "cap" or not isinstance(part, _Revolve)
        else _Revolve(part.name, True, part.points, cap_feature.feature_id, part.axis_feature_id)
        for part in spec.parts
    )
    spec = _Spec(spec.package_family, model.features, model.parameters, parts)
    merged = {**design.extra, **(extra or {})}
    return _realize(
        "closure",
        design.preset,
        parameters,
        spec,
        model,
        (*design.history, model.revision_id),
        merged,
    )


# ------------------------------------------------------------------ reopen persisted


def load_family_document(document: Mapping[str, Any]) -> FamilyDesign:
    """Rebuild a persisted family revision (exact core document + its workflow parameters)."""
    workflow = document.get("package_family_workflow")
    if not isinstance(workflow, Mapping) or workflow.get("contract") != WORKFLOW_CONTRACT:
        raise PackageFamilyError("not a package-family Design Model revision")
    family = str(workflow.get("family"))
    if family not in FAMILIES:
        raise PackageFamilyError(f"unknown package family {family}")
    try:
        core = deserialize_design_model(str(document["design_document"]).encode("utf-8"))
    except (KeyError, ValueError) as error:
        raise PackageFamilyError(f"family design document is invalid: {error}") from error
    model = core.model
    if model.as_dict() != document.get("model") or model.revision_id != document.get(
        "design_model_revision_id"
    ):
        raise PackageFamilyError("family design document does not match its record")
    parameters: dict[str, Any] = dict(workflow.get("parameters_mm_unverified", {}))
    if family == "closure":
        parameters["container_profile"] = [tuple(item) for item in workflow["container_profile"]]
        parameters["container_features"] = tuple(workflow["container_features"])
    history = tuple(document.get("revision_history", ()) or (model.revision_id,))
    extra = {
        key: value
        for key, value in workflow.items()
        if key
        in {"assembly", "closure_replacement", "artwork", "pouch_family", "jerrycan_body_fit"}
    }
    preset = str(workflow.get("preset", ""))
    if family == "pouch":
        root = model.standalone_root
        assert root is not None
        values = {k: float(v) for k, v in parameters.items()}
        dims = PouchFamilyDimensions(**{name: values[name] for name, _ in PARAMETERS["pouch"]})
        rebuilt = build_pouch_family(
            root,
            dims,
            component_id="pouch",
            actor_id=model.actor_id,
            reason="reopen",
            created_at_utc=model.created_at_utc,
            front_bulge=0.25 * dims.thickness,
            back_bulge=0.25 * dims.thickness,
        )
        # ponytail: the reopened pouch keeps the exact persisted model; the preview proxy is
        # regenerated from the same dimensions (the proxy is disposable in core).
        revision = PouchFamilyRevision(
            model,
            dims,
            rebuilt.preview,
            "pouch",
            rebuilt.front_artwork_feature_id,
            rebuilt.back_artwork_feature_id,
            rebuilt.front_bulge,
            rebuilt.back_bulge,
            rebuilt.artwork_anchors,
        )
        _POUCH_REVISIONS[model.revision_id] = revision
        return FamilyDesign(
            family,
            preset,
            values,
            model,
            (),
            str(document["design_document"]).encode("utf-8"),
            history,
            rebuilt.preview.mesh,
            extra,
        )
    if family == "jerrycan" and "jerrycan_body_fit" in extra:
        loft = core.operations[0]
        by_id = {item.section_id: item for item in core.cross_sections}
        inputs = tuple(
            LoftSectionInput(feature_id, by_id[section_id], z)
            for feature_id, section_id, z in zip(
                loft.parent_feature_ids, loft.input_ids, loft.section_positions, strict=False
            )
        )
        representation = loft_design_model_to_brep(model, inputs, loft, ruled=True)
        part = FamilyPart(
            "body", False, loft, representation, tessellate_brep_preview(model, representation)
        )
        return FamilyDesign(
            family,
            preset,
            parameters,
            model,
            (part,),
            str(document["design_document"]).encode("utf-8"),
            history,
            None,
            extra,
        )
    container = model if family == "closure" else None
    spec = _spec_for(family, parameters, project_id=model.project_id, container=container)
    if family == "closure":
        cap_id, _pid, values = current_cap(
            FamilyDesign(family, preset, parameters, model, (), b"", history)
        )
        parameters.update(
            {
                k: float(values[k])
                for k in ("closure_line", "cap_diameter", "cap_height")
                if k in values
            }
        )
        spec = _closure_spec(parameters, model)
        spec = _Spec(
            spec.package_family,
            model.features,
            model.parameters,
            tuple(
                _Revolve(p.name, True, p.points, cap_id, p.axis_feature_id)
                if isinstance(p, _Revolve) and p.name == "cap"
                else p
                for p in spec.parts
            ),
        )
    design = _realize(family, preset, parameters, spec, model, history, extra)
    stored = {
        str(item.get("operation_id"))
        for item in workflow.get("parts", [])
        if isinstance(item, Mapping)
    }
    if stored != {item.operation.operation_id for item in design.parts}:
        raise PackageFamilyError("family geometry no longer reproduces the persisted operations")
    return design


def describe(design: FamilyDesign) -> str:
    dims = design.overall_dimensions()
    parent = (
        f"standalone root {design.model.standalone_root.revision_id[:40]}…"
        if design.model.standalone_root is not None
        else f"Scan Master {str(design.model.fitted_to_scan_master_revision_id)[:30]}…"
    )
    parts = ", ".join(item.name for item in design.parts) or "preview proxy only (no BREP)"
    return (
        f"{FAMILIES[design.family]}: revision {design.model.revision_id[:34]}…; "
        f"H {dims['height']:.1f} × W {dims['width']:.1f} × D {dims['depth']:.1f} mm_unverified; "
        f"parent {design.provenance} ({parent}); parts: {parts}; "
        "physical validation DEFERRED_OWNER_VALIDATION; mold use not authorized."
    )


__all__ = [
    "FAMILIES",
    "PARAMETERS",
    "PRESETS",
    "FamilyDesign",
    "FamilyPart",
    "PackageFamilyError",
    "attach_pouch_artwork",
    "closure_defaults",
    "closure_mating_references",
    "container_context",
    "create_closure",
    "create_standalone",
    "create_tube_on_scan_master",
    "default_parameters",
    "describe",
    "edit",
    "fit_jerrycan_on_scan_master",
    "load_family_document",
    "replacement_base",
]
