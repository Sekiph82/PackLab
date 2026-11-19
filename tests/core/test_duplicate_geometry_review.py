"""PL-0411 duplicate-geometry review on synthetic fixtures with known metric ground truth.

All fixtures are SIMULATION ONLY (procedural PET-bottle / HDPE-jerrycan proxies in mm, seeded
noise). They test code behaviour and limits; they are not factory or physical validation.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import replace

import pytest

from packlab_core import duplicate_geometry_review as review_module
from packlab_core.design_model import PackageFamily, create_standalone_design_model_revision
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_preview import DesignPreview
from packlab_core.duplicate_geometry_review import (
    PHYSICAL_EVIDENCE_PENDING,
    AuthorityKind,
    DuplicateDecisionRecord,
    DuplicateGeometryError,
    DuplicateGeometryReview,
    DuplicateReviewPolicy,
    LibraryGeometryEntry,
    build_reuse_plan,
    review_duplicate_geometry,
)
from packlab_core.geometry_adapter import (
    CapabilityStatus,
    InvalidGeometry,
    Open3DGeometryAdapter,
    TriangleMeshData,
    probe_open3d,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

pytestmark = pytest.mark.skipif(
    probe_open3d().status is not CapabilityStatus.AVAILABLE, reason="pinned Open3D required"
)

PROJECT = "bf0f6a8e-3b7e-4d55-9a52-1d2f0b9b4411"
NOW = "2026-11-19T12:00:00Z"
SEGMENTS = 32


# ------------------------------------------------------------------ synthetic fixtures (mm)


def _bottle(
    *, height_scale=1.0, cap_radius=15.0, start_z=0.0, segments=SEGMENTS
) -> TriangleMeshData:
    """500 ml PET-style bottle: 70 mm body, shoulder, 28 mm neck, cap; closed unless start_z>0."""

    profile = [(35.0, float(z)) for z in range(0, 151, 10) if z >= start_z]
    profile += [(35.0 - 21.0 * t / 4, 150.0 + 10.0 * t) for t in range(1, 5)]
    profile += [(14.0, 195.0), (14.0, 205.0), (cap_radius, 205.0)]
    profile += [(cap_radius, 215.0), (cap_radius, 225.0)]
    vertices: list[tuple[float, float, float]] = []
    for r, z in profile:
        for j in range(segments):
            a = 2 * math.pi * j / segments
            vertices.append((r * math.cos(a), r * math.sin(a), z * height_scale))
    triangles: list[tuple[int, int, int]] = []
    for i in range(len(profile) - 1):
        for j in range(segments):
            a, b = i * segments + j, i * segments + (j + 1) % segments
            c, d = a + segments, b + segments
            triangles += [(a, b, d), (a, d, c)]
    last = (len(profile) - 1) * segments
    top = len(vertices)
    vertices.append((0.0, 0.0, 225.0 * height_scale))
    triangles += [(top, last + j, last + (j + 1) % segments) for j in range(segments)]
    if start_z == 0.0:
        bottom = len(vertices)
        vertices.append((0.0, 0.0, 0.0))
        triangles += [(bottom, (j + 1) % segments, j) for j in range(segments)]
    return TriangleMeshData(tuple(vertices), tuple(triangles))


def _box(bounds, offset):
    x0, x1, y0, y1, z0, z1 = (float(b) for b in bounds)
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    faces = [
        (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
        (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
    ]  # fmt: skip
    return v, [(a + offset, b + offset, c + offset) for a, b, c in faces]


def _jerrycan(*, mirrored=False) -> TriangleMeshData:
    """20 l HDPE-style jerrycan proxy: body, off-centre handle, corner spout (chiral)."""

    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for box in (
        (0, 300, 0, 180, 0, 380),
        (200, 280, 60, 120, 380, 440),
        (20, 70, 110, 160, 380, 420),
    ):
        v, f = _box(box, len(vertices))
        vertices += v
        triangles += f
    if mirrored:
        vertices = [(x, 180.0 - y, z) for x, y, z in vertices]
        triangles = [(a, c, b) for a, b, c in triangles]
    return TriangleMeshData(tuple(vertices), tuple(triangles))


def _posed(mesh: TriangleMeshData, *, seed: int, noise_mm=0.05) -> TriangleMeshData:
    """Apply a seeded proper rigid pose and isotropic Gaussian vertex noise."""

    rng = random.Random(seed)
    axis = [rng.gauss(0, 1) for _ in range(3)]
    norm = math.sqrt(sum(x * x for x in axis))
    x, y, z = (c / norm for c in axis)
    angle = rng.uniform(0.3, 2.8)
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    r = (
        (t * x * x + c, t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )
    shift = [rng.uniform(-500, 500) for _ in range(3)]
    vertices = tuple(
        tuple(
            sum(r[i][k] * p[k] for k in range(3)) + shift[i] + rng.gauss(0, noise_mm)
            for i in range(3)
        )
        for p in mesh.vertices
    )
    return TriangleMeshData(vertices, mesh.triangles)  # type: ignore[arg-type]


def _entry(entry_id, mesh, skus, *, family=PackageFamily.BOTTLE, coverage=1.0, **overrides):
    values = dict(
        entry_id=entry_id,
        authority_kind=AuthorityKind.SCAN_MASTER,
        authority_revision_id=f"scan-master:{hashlib.sha256(entry_id.encode()).hexdigest()}",
        family=family,
        sku_ids=tuple(skus),
        scale_state=ScaleState.METRIC_UNVERIFIED,
        coordinate_unit="mm_unverified",
        mesh=mesh,
        coverage_fraction=coverage,
        simulation_only=True,
    )
    values.update(overrides)
    return LibraryGeometryEntry(**values)


def _scan_master_entry(entry_id, mesh, skus):
    revision_id = f"scan-master:{hashlib.sha256(entry_id.encode()).hexdigest()}"
    scan = ScanMasterRevision(
        revision_id,
        PROJECT,
        mesh,
        {
            "scan_master_revision_id": revision_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(mesh),
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-provenance:pl0411-sim",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    return LibraryGeometryEntry.from_scan_master(
        scan,
        entry_id=entry_id,
        family=PackageFamily.BOTTLE,
        sku_ids=tuple(skus),
        coverage_fraction=1.0,
        simulation_only=True,
    )


def _nominal_model():
    root = create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:pl0411-sim",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-choice:mm_unverified",
        actor_id="operator-1",
        reason="PL-0411 simulated nominal bottle.",
        created_at_utc=NOW,
    )
    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="PL-0411 simulated nominal bottle.",
        created_at_utc=NOW,
    )


def _preview(model, mesh, **overrides):
    values = dict(
        mesh=mesh,
        model_revision_id=model.revision_id,
        scan_master_revision_id=None,
        scan_master_geometry_sha256=None,
        parent_binding_revision_id=None,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status="DEFERRED_OWNER_VALIDATION",
        mold_use_authorized=False,
        feature_vertex_indices=(),
        standalone_root_revision_id=model.standalone_root.revision_id,
    )
    values.update(overrides)
    return DesignPreview(**values)


def _design_model_entry(entry_id, mesh, skus):
    model = _nominal_model()
    return LibraryGeometryEntry.from_design_model(
        model, _preview(model, mesh), entry_id=entry_id, sku_ids=tuple(skus), simulation_only=True
    )


# Ground truth: entry id -> physical package identity in the simulation.
LIBRARY = {
    "bottle-a-pose1": ("BOTTLE_500", _scan_master_entry, _bottle(), ("SKU-WATER-BLUE",)),
    "bottle-a-pose2": (
        "BOTTLE_500",
        _scan_master_entry,
        _posed(_bottle(), seed=11),
        ("SKU-WATER-RED", "SKU-WATER-PROMO"),
    ),
    # Nominal Design Model tessellation is finer (48 vs 32 segments): tessellation-independent.
    "bottle-a-nominal": (
        "BOTTLE_500",
        _design_model_entry,
        _bottle(segments=48),
        ("SKU-JUICE-LABEL",),
    ),
    "bottle-tall-2pct": (
        "BOTTLE_TALL",
        _scan_master_entry,
        _posed(_bottle(height_scale=1.02), seed=12),
        ("SKU-TALL",),
    ),
    "bottle-wide-cap": (
        "BOTTLE_WIDE_CAP",
        _scan_master_entry,
        _posed(_bottle(cap_radius=16.0), seed=13),
        ("SKU-SPORTCAP",),
    ),
}


BOTTLE_A = ("bottle-a-nominal", "bottle-a-pose1", "bottle-a-pose2")


@pytest.fixture(scope="module")
def review():
    entries = [builder(eid, mesh, skus) for eid, (_, builder, mesh, skus) in LIBRARY.items()]
    entries += [
        _entry("bottle-partial", _posed(_bottle(start_z=60.0), seed=14), ("SKU-PARTIAL",),
               coverage=0.72),
        _entry("can-left", _jerrycan(), ("SKU-OIL-20L",), family=PackageFamily.JERRYCAN),
        _entry("can-left-posed", _posed(_jerrycan(), seed=15), ("SKU-OIL-20L-EXPORT",),
               family=PackageFamily.JERRYCAN),
        _entry("can-right", _jerrycan(mirrored=True), ("SKU-OIL-20L-RH",),
               family=PackageFamily.JERRYCAN),
    ]  # fmt: skip
    return review_duplicate_geometry(entries)


def _pair(report, left, right):
    for pair in report["pairs"]:
        if set(pair["entry_ids"]) == {left, right}:
            return pair
    raise AssertionError((left, right))


def _group(report, *ids):
    return next(g for g in report["groups"] if g["member_entry_ids"] == sorted(ids))


# ------------------------------------------------------------------ ground-truth outcomes


def test_same_bottle_different_pose_noise_and_artwork_is_proposed(review) -> None:
    report = review.as_dict()
    pair = _pair(report, "bottle-a-pose1", "bottle-a-pose2")
    assert pair["decision"] == "PROPOSED_DUPLICATE"
    assert pair["registration"]["rms_deviation"] <= 0.25
    assert pair["registration"]["max_deviation"] <= 0.75
    # Design Model tessellation of the same nominal shape is also matched (different authority).
    assert _pair(report, "bottle-a-pose1", "bottle-a-nominal")["decision"] == "PROPOSED_DUPLICATE"
    group = _group(report, *BOTTLE_A)
    assert group["decision"] == "PROPOSED_DUPLICATE"
    assert group["sku_ids"] == [
        "SKU-JUICE-LABEL", "SKU-WATER-BLUE", "SKU-WATER-PROMO", "SKU-WATER-RED",
    ]  # fmt: skip
    assert group["requires_owner_decision_record"] is True


def test_two_percent_taller_bottle_is_distinct(review) -> None:
    report = review.as_dict()
    pair = _pair(report, "bottle-a-pose1", "bottle-tall-2pct")
    assert pair["decision"] == "DISTINCT"
    assert "extent_mismatch" in pair["reasons"]
    # It only appears paired with the partial scan, which cannot rule it out geometrically.
    tall_groups = [g for g in report["groups"] if "bottle-tall-2pct" in g["member_entry_ids"]]
    assert [g["member_entry_ids"] for g in tall_groups] == [["bottle-partial", "bottle-tall-2pct"]]
    assert tall_groups[0]["decision"] == "NEEDS_HUMAN_REVIEW"


def test_two_percent_taller_bottle_is_distinct_by_registration_when_screens_relaxed() -> None:
    policy = DuplicateReviewPolicy(invariant_relative_tolerance=0.05, extent_absolute_tolerance=20)
    report = review_duplicate_geometry(
        [
            _entry("a", _bottle(), ("SKU-A",)),
            _entry("b", _posed(_bottle(height_scale=1.02), seed=21), ("SKU-B",)),
        ],
        policy=policy,
    ).as_dict()
    pair = report["pairs"][0]
    assert pair["decision"] != "PROPOSED_DUPLICATE"
    assert pair["registration"]["max_deviation"] > 0.75
    # Scaling is never applied: the best rigid transform stays a proper rotation (det +1).
    t = pair["registration"]["transform_source_to_target"]
    r = [t[0:3], t[4:7], t[8:11]]
    det = (
        r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
        - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
        + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0])
    )
    assert det == pytest.approx(1.0, abs=1e-6)


def test_cap_only_difference_is_not_proposed(review) -> None:
    pair = _pair(review.as_dict(), "bottle-a-pose1", "bottle-wide-cap")
    assert pair["decision"] in {"DISTINCT", "NEEDS_HUMAN_REVIEW"}
    assert pair["registration"]["max_deviation"] > 0.75


def test_partial_coverage_needs_human_review(review) -> None:
    report = review.as_dict()
    pair = _pair(report, "bottle-a-pose1", "bottle-partial")
    assert pair["decision"] == "NEEDS_HUMAN_REVIEW"
    assert pair["reasons"] == ["partial_coverage_cannot_confirm_duplicate"]
    partial = next(e for e in report["entries"] if e["entry_id"] == "bottle-partial")
    assert partial["invariants"]["partial_coverage"] is True
    assert partial["invariants"]["boundary_edge_count"] == SEGMENTS
    # Review pairs never swallow the confirmed duplicate group (no transitive merging).
    group = _group(report, "bottle-a-pose1", "bottle-partial")
    assert group["decision"] == "NEEDS_HUMAN_REVIEW"
    assert "partial_coverage_cannot_confirm_duplicate" in group["reasons"]
    assert _group(report, *BOTTLE_A)["decision"] == "PROPOSED_DUPLICATE"


def test_mirrored_jerrycan_is_never_merged(review) -> None:
    report = review.as_dict()
    assert _pair(report, "can-left", "can-left-posed")["decision"] == "PROPOSED_DUPLICATE"
    for other in ("can-left", "can-left-posed"):
        pair = _pair(report, other, "can-right")
        assert pair["decision"] == "DISTINCT"
        assert pair["reasons"] == ["mirror_image_handedness_differs"]
        assert pair["mirror_registration"]["max_deviation"] <= 0.75
        assert pair["registration"]["max_deviation"] > 10.0
    assert all("can-right" not in g["member_entry_ids"] for g in report["groups"])
    # Mirror images share every pose invariant, so only the rotation constraint separates them.
    by_id = {e["entry_id"]: e["invariants"] for e in report["entries"]}
    assert by_id["can-left"]["principal_extents_sorted"] == pytest.approx(
        by_id["can-right"]["principal_extents_sorted"]
    )


def test_families_are_never_cross_compared(review) -> None:
    report = review.as_dict()
    assert all(not ({"can-left", "bottle-a-pose1"} <= set(p["entry_ids"])) for p in report["pairs"])


def test_report_is_versioned_digest_bound_and_simulation_labelled(review) -> None:
    report = review.as_dict()
    assert report["contract"] == "packlab.duplicate-geometry-review.v1"
    assert report["version"] == 1
    assert report["simulation_only"] is True
    assert report["physical_validation_status"] == PHYSICAL_EVIDENCE_PENDING
    assert report["auto_merge_performed"] is False
    assert report["deletion_performed"] is False
    assert report["authority_changes"] == "NONE"
    assert review.sha256 == hashlib.sha256(review.canonical_json).hexdigest()
    with pytest.raises(AttributeError):
        review.canonical_json = b"{}"


def test_review_is_deterministic_and_order_independent() -> None:
    entries = [_entry("a", _bottle(), ("SKU-A",)), _entry("b", _posed(_bottle(), seed=3), ("B",))]
    first = review_duplicate_geometry(entries)
    second = review_duplicate_geometry(list(reversed(entries)))
    assert first.sha256 == second.sha256


# ------------------------------------------------------------------ decisions and reuse plan


def test_reuse_plan_only_from_approved_records(review) -> None:
    report = review.as_dict()
    bottle = _group(report, *BOTTLE_A)
    jerry = _group(report, "can-left", "can-left-posed")

    plan_none = build_reuse_plan(review, [])
    assert plan_none["approved_reuse"] == []
    assert set(plan_none["undecided_group_ids"]) == {g["group_id"] for g in report["groups"]}

    approve = DuplicateDecisionRecord(
        review.sha256, bottle["group_id"], "APPROVE", "owner-1", NOW,
        "Same blow mould; label-only SKU difference.", canonical_entry_id="bottle-a-pose1",
    )  # fmt: skip
    reject = DuplicateDecisionRecord(
        review.sha256, jerry["group_id"], "REJECT", "operator-7", NOW, "Needs a fresh scan."
    )
    plan = build_reuse_plan(review, [approve, reject])
    assert [item["reuse_for_sku_ids"] for item in plan["approved_reuse"]] == [
        ["SKU-JUICE-LABEL", "SKU-WATER-BLUE", "SKU-WATER-PROMO", "SKU-WATER-RED"]
    ]
    item = plan["approved_reuse"][0]
    assert item["scan_once_entry_id"] == "bottle-a-pose1"
    assert item["scan_once_authority_kind"] == "SCAN_MASTER"
    assert item["scan_once_geometry_provenance"] == "SCAN_MASTER_MANIFEST_DIGEST"
    assert item["approved_by"] == "owner-1"
    assert plan["rejected_group_ids"] == [jerry["group_id"]]
    assert plan["authority_changes"] == "NONE"
    assert plan["existing_scan_master_authority_preserved"] is True
    assert plan["auto_merge_performed"] is False
    assert plan["physical_validation_status"] == PHYSICAL_EVIDENCE_PENDING
    assert len(plan["plan_sha256"]) == 64


def test_reuse_plan_fails_closed(review) -> None:
    report = review.as_dict()
    jerry = _group(report, "can-left", "can-left-posed")
    partial = _group(report, "bottle-a-nominal", "bottle-partial")
    bottle = _group(report, *BOTTLE_A)
    cap = _group(report, "bottle-a-nominal", "bottle-wide-cap")

    def record(**changes):
        base = dict(
            review_sha256=review.sha256,
            group_id=jerry["group_id"],
            decision="APPROVE",
            actor_id="owner-1",
            decided_at_utc=NOW,
            reason="ok",
            canonical_entry_id="can-left",
        )
        return DuplicateDecisionRecord(**(base | changes))

    cases = [
        ([record(review_sha256="0" * 64)], "decision_review_digest_mismatch"),
        ([record(group_id="duplicate-group:unknown")], "decision_group_unknown"),
        ([record(decision="REJECT", canonical_entry_id=None), record()], "decision_group_conflict"),
        ([record(canonical_entry_id="can-right")], "canonical_entry_not_group_member"),
        (
            [record(group_id=partial["group_id"], canonical_entry_id="bottle-partial")],
            "canonical_entry_partial_coverage",
        ),
        (
            [
                record(group_id=bottle["group_id"], canonical_entry_id="bottle-a-pose1"),
                record(group_id=cap["group_id"], canonical_entry_id="bottle-a-nominal"),
            ],
            "approved_groups_overlap",
        ),
        # Directly constructed entries are caller-asserted, never a verified scan-once source.
        ([record()], "canonical_entry_authority_unverified"),
    ]
    for records, message in cases:
        with pytest.raises(DuplicateGeometryError, match=message):
            build_reuse_plan(review, records)
    for bad in (
        dict(actor_id=""),
        dict(decision="MERGE"),
        dict(canonical_entry_id=None),
        dict(decided_at_utc="yesterday"),
        dict(reason=" "),
    ):
        with pytest.raises(DuplicateGeometryError):
            record(**bad)


# ------------------------------------------------------------------ fail-closed inputs


def test_scale_and_unit_inputs_fail_closed() -> None:
    a = _entry("a", _bottle(), ("SKU-A",))
    b = _entry("b", _bottle(), ("SKU-B",))
    relative = dict(scale_state=ScaleState.RELATIVE, coordinate_unit="reconstruction_units")
    verified = dict(scale_state=ScaleState.METRIC_VERIFIED, coordinate_unit="mm")
    cases = [
        ([replace(a, **relative), replace(b, **relative)], "relative_scale_forbidden"),
        ([a, replace(b, **verified)], "mixed_scale_states"),
        ([a, replace(b, scale_state=None, coordinate_unit=None)], "scale_state_missing"),
        ([a, replace(b, coordinate_unit="in")], "coordinate_unit_mismatch"),
        ([a, replace(b, entry_id="a")], "entry_id_duplicate"),
        ([a], "at_least_two_typed_entries_required"),
    ]
    for entries, message in cases:
        with pytest.raises(DuplicateGeometryError, match=message):
            review_duplicate_geometry(entries)


def test_entry_bound_is_enforced_before_any_geometry_work() -> None:
    entries = [_entry(f"e{i}", _bottle(), (f"SKU-{i}",)) for i in range(3)]
    with pytest.raises(DuplicateGeometryError, match="entry_bound_exceeded"):
        review_duplicate_geometry(entries, policy=DuplicateReviewPolicy(max_entries=2))
    with pytest.raises(DuplicateGeometryError, match="max_entries_invalid"):
        DuplicateReviewPolicy(max_entries=10_000)


def test_non_finite_geometry_fails_closed() -> None:
    with pytest.raises(ValueError):
        TriangleMeshData(((math.nan, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), ((0, 1, 2),))
    mesh = _bottle()
    object.__setattr__(mesh, "vertices", ((math.inf, 0.0, 0.0), *mesh.vertices[1:]))
    with pytest.raises(DuplicateGeometryError, match="geometry_non_finite"):
        _entry("a", mesh, ("SKU-A",))


def test_scan_master_digest_mismatch_fails_closed() -> None:
    mesh = _bottle()
    scan = ScanMasterRevision(
        "scan-master:x",
        PROJECT,
        mesh,
        {
            "scan_master_revision_id": "scan-master:x",
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": "0" * 64,
            "scale_state": "metric-unverified",
        },
    )
    with pytest.raises(DuplicateGeometryError, match="scan_master_manifest_invalid"):
        LibraryGeometryEntry.from_scan_master(
            scan,
            entry_id="x",
            family=PackageFamily.BOTTLE,
            sku_ids=("SKU-X",),
            coverage_fraction=1.0,
            simulation_only=True,
        )


@pytest.mark.parametrize("seed", [31, 32, 33])
def test_duplicate_detection_is_stable_across_poses(seed) -> None:
    family = PackageFamily.JERRYCAN
    report = review_duplicate_geometry(
        [
            _entry("a", _posed(_jerrycan(), seed=seed), ("SKU-A",), family=family),
            _entry("b", _posed(_jerrycan(), seed=seed + 100), ("SKU-B",), family=family),
            _entry(
                "m", _posed(_jerrycan(mirrored=True), seed=seed + 200), ("SKU-M",), family=family
            ),
        ]
    ).as_dict()
    assert _pair(report, "a", "b")["decision"] == "PROPOSED_DUPLICATE"
    assert _pair(report, "a", "m")["decision"] == "DISTINCT"
    assert _pair(report, "b", "m")["decision"] == "DISTINCT"


# ------------------------------------------------------------------ review findings (V01)


def test_authority_kind_and_provenance_are_reported(review) -> None:
    by_id = {e["entry_id"]: e for e in review.as_dict()["entries"]}
    assert by_id["bottle-a-nominal"]["authority_kind"] == "DESIGN_MODEL"
    assert by_id["bottle-a-nominal"]["geometry_provenance"] == "DESIGN_PREVIEW_BOUND_TO_REVISION"
    assert by_id["bottle-a-pose1"]["authority_kind"] == "SCAN_MASTER"
    assert by_id["bottle-a-pose1"]["authority_verified"] is True
    assert by_id["can-left"]["authority_verified"] is False
    assert by_id["can-left"]["geometry_provenance"] == "CALLER_ASSERTED_UNVERIFIED"


def test_design_preview_must_be_bound_to_the_revision() -> None:
    model = _nominal_model()
    for preview in (
        _preview(model, _bottle(), model_revision_id="design-model:other"),
        _preview(model, _bottle(), standalone_root_revision_id="standalone-root:other"),
    ):
        with pytest.raises(DuplicateGeometryError, match="design_preview_not_bound_to_revision"):
            LibraryGeometryEntry.from_design_model(
                model, preview, entry_id="x", sku_ids=("SKU-X",), simulation_only=True
            )


def test_replace_drops_verified_provenance() -> None:
    entry = _scan_master_entry("x", _bottle(), ("SKU-X",))
    assert entry.authority_verified is True
    assert replace(entry, sku_ids=("SKU-Y",)).authority_verified is False


def _column_and_sliver(seed):
    column, faces = _box((0, 100, 0, 100, 0, 300), 0)
    column_mesh = TriangleMeshData(tuple(column), tuple(faces))
    # Open 5 mm strip on the x=0 face running along its 100 x 300 diagonal (length ~316 mm,
    # longer than every sorted PCA extent of the column, yet a genuine subset of its surface).
    steps = 30
    vertices = []
    for i in range(steps + 1):
        t = i / steps
        y, z = 2.5 + 95.0 * t, 300.0 * t
        vertices += [(0.0, y - 2.5, z), (0.0, y + 2.5, z)]
    triangles = []
    for i in range(steps):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        triangles += [(a, b, d), (a, d, c)]
    sliver = _posed(TriangleMeshData(tuple(vertices), tuple(triangles)), seed=seed, noise_mm=0.0)
    return column_mesh, sliver


@pytest.mark.parametrize("seed", [41, 42, 43])
def test_partial_subset_sliver_reaches_human_review(seed) -> None:
    column, sliver = _column_and_sliver(seed)
    family = PackageFamily.OTHER
    report = review_duplicate_geometry(
        [
            _entry("column", column, ("SKU-COL",), family=family),
            _entry("sliver", sliver, ("SKU-SLV",), family=family, coverage=0.05),
        ]
    ).as_dict()
    by_id = {e["entry_id"]: e["invariants"] for e in report["entries"]}
    assert max(by_id["sliver"]["principal_extents_sorted"]) > 300.0
    pair = report["pairs"][0]
    assert pair["decision"] == "NEEDS_HUMAN_REVIEW"
    assert pair["reasons"] == ["partial_coverage_cannot_confirm_duplicate"]


def test_partial_larger_than_complete_diameter_is_distinct() -> None:
    family = PackageFamily.OTHER
    big, faces = _box((0, 100, 0, 100, 0, 600), 0)
    small, small_faces = _box((0, 100, 0, 100, 0, 300), 0)
    report = review_duplicate_geometry(
        [
            _entry("small", TriangleMeshData(tuple(small), tuple(small_faces)), ("S",),
                   family=family),
            _entry("big-partial", TriangleMeshData(tuple(big), tuple(faces)), ("B",),
                   family=family, coverage=0.5),
        ]
    ).as_dict()  # fmt: skip
    assert report["pairs"][0]["decision"] == "DISTINCT"
    assert report["pairs"][0]["reasons"] == ["partial_larger_than_complete_geometry_diameter"]


def test_declared_low_coverage_on_closed_mesh_is_partial() -> None:
    report = review_duplicate_geometry(
        [
            _entry("a", _bottle(), ("SKU-A",)),
            _entry("b", _posed(_bottle(), seed=5), ("SKU-B",), coverage=0.9),
        ]
    ).as_dict()
    by_id = {e["entry_id"]: e["invariants"] for e in report["entries"]}
    assert by_id["b"]["boundary_edge_count"] == 0
    assert by_id["b"]["partial_coverage"] is True
    assert report["pairs"][0]["decision"] == "NEEDS_HUMAN_REVIEW"
    assert report["pairs"][0]["registration"] is None


def test_transitive_chain_is_not_merged() -> None:
    report = review_duplicate_geometry(
        [
            _entry("a", _bottle(), ("SKU-A",)),
            _entry("b", _posed(_bottle(height_scale=1.003), seed=51), ("SKU-B",)),
            _entry("c", _posed(_bottle(height_scale=1.006), seed=52), ("SKU-C",)),
        ]
    ).as_dict()
    assert _pair(report, "a", "b")["decision"] == "PROPOSED_DUPLICATE"
    assert _pair(report, "b", "c")["decision"] == "PROPOSED_DUPLICATE"
    assert _pair(report, "a", "c")["decision"] != "PROPOSED_DUPLICATE"
    group = _group(report, "a", "b", "c")
    assert group["decision"] == "NEEDS_HUMAN_REVIEW"
    assert "group_not_fully_confirmed_pairwise" in group["reasons"]


def test_review_tolerance_below_rms_tolerance_is_rejected() -> None:
    with pytest.raises(DuplicateGeometryError, match="policy_tolerances_inconsistent"):
        DuplicateReviewPolicy(rms_tolerance=0.25, review_rms_tolerance=0.1)


def test_report_policy_lists_only_applied_registration_parameters(review) -> None:
    registration = review.as_dict()["policy"]["registration"]
    assert "maximum_inlier_rmse" not in registration
    assert "minimum_inlier_count" not in registration
    assert registration["scaling_enabled"] is False


def test_simulation_flag_is_true_if_any_entry_is_simulated() -> None:
    # Different families: no geometric comparison runs, only the report labelling.
    def entries(flags):
        return [
            _entry("a", _bottle(), ("SKU-A",), simulation_only=flags[0]),
            _entry("b", _bottle(), ("SKU-B",), family=PackageFamily.JAR, simulation_only=flags[1]),
        ]

    assert review_duplicate_geometry(entries((True, False))).as_dict()["simulation_only"] is True
    assert review_duplicate_geometry(entries((False, False))).as_dict()["simulation_only"] is False


def test_triangle_bound_is_enforced(monkeypatch) -> None:
    monkeypatch.setattr(review_module, "_MAX_TRIANGLES", 10)
    with pytest.raises(DuplicateGeometryError, match="mesh_triangle_bound_exceeded"):
        _entry("a", _bottle(), ("SKU-A",))


class _BrokenAdapter(Open3DGeometryAdapter):
    def register_point_clouds(self, *args, **kwargs):
        raise InvalidGeometry("simulated adapter failure")


def test_adapter_errors_map_to_registration_failed_closed() -> None:
    with pytest.raises(DuplicateGeometryError, match="registration_failed_closed"):
        review_duplicate_geometry(
            [_entry("a", _bottle(), ("SKU-A",)), _entry("b", _bottle(), ("SKU-B",))],
            adapter=_BrokenAdapter(),
        )


def test_reuse_plan_checks_contract_and_blocks_distinct_pairs(review) -> None:
    report = review.as_dict()

    def reissued(mutate):
        body = json.loads(review.canonical_json)
        mutate(body)
        return DuplicateGeometryReview(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )

    def approve(target, group_id):
        return DuplicateDecisionRecord(
            target.sha256, group_id, "APPROVE", "owner-1", NOW, "ok",
            canonical_entry_id="bottle-a-pose1",
        )  # fmt: skip

    bottle_id = _group(report, *BOTTLE_A)["group_id"]
    for key, value in (("contract", "packlab.other.v1"), ("version", 2)):
        forged = reissued(lambda body, k=key, v=value: body.__setitem__(k, v))
        with pytest.raises(DuplicateGeometryError, match="review_contract_or_version_unsupported"):
            build_reuse_plan(forged, [approve(forged, bottle_id)])

    def add_distinct(body):
        group = next(g for g in body["groups"] if g["group_id"] == bottle_id)
        group["pairs"][0]["decision"] = "DISTINCT"

    tainted = reissued(add_distinct)
    with pytest.raises(DuplicateGeometryError, match="approval_blocked_distinct_pair_in_group"):
        build_reuse_plan(tainted, [approve(tainted, bottle_id)])
