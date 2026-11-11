"""PL-0430 core half: AR preview package built from a real tessellated Design Model."""

from __future__ import annotations

import hashlib
import json

import pytest
from tests.core.test_cad_brep import _inputs

from packlab_core.ar_preview import AR_PREVIEW_CONTRACT, ArPreviewError, build_ar_preview_package
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_preview import tessellate_brep_preview
from packlab_core.reconstruction import ScaleState


def _preview(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    return tessellate_brep_preview(model, revolve_design_model_to_brep(model, profile, operation))


def test_package_is_deterministic_digest_bound_and_carries_no_authority() -> None:
    preview = _preview()
    first = build_ar_preview_package(preview)
    assert first == build_ar_preview_package(preview)
    document = json.loads(first)
    assert document["contract"] == AR_PREVIEW_CONTRACT
    digest = document.pop("content_sha256")
    body = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert hashlib.sha256(body.encode("ascii")).hexdigest() == digest
    assert document["source"]["design_model_revision_id"] == preview.source_design_model_revision_id
    assert document["authority"] == {
        "class": "AR_VISUAL_REFERENCE_ONLY",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "scan_master_replaced": False,
        "on_device_scale_verified": False,
    }


def test_mm_geometry_becomes_metres_y_up_resting_on_its_base() -> None:
    # Fixture: revolve of radius 5 mm, height 100 mm about z.
    document = json.loads(build_ar_preview_package(_preview()))
    positions = document["positions"]
    xs, ys, zs = positions[0::3], positions[1::3], positions[2::3]
    assert document["display_scale_basis"] == "MM_UNVERIFIED_TO_METRES_DISPLAY_ONLY"
    assert min(ys) == pytest.approx(0.0, abs=1e-7)
    assert max(ys) == pytest.approx(0.1, abs=1e-6)  # 100 mm tall, now along RealityKit +y
    # 10 mm diameter; the tessellated polygon may sit just inside the true circle.
    assert max(xs) - min(xs) == pytest.approx(0.01, abs=1e-4)
    assert max(zs) - min(zs) == pytest.approx(0.01, abs=1e-4)
    assert (max(xs) + min(xs)) / 2 == pytest.approx(0.0, abs=1e-7)
    assert len(document["indices"]) % 3 == 0
    assert max(document["indices"]) < len(positions) // 3


def test_relative_geometry_is_shown_at_a_labelled_nominal_size() -> None:
    document = json.loads(build_ar_preview_package(_preview(ScaleState.RELATIVE)))
    assert document["display_scale_basis"] == "RELATIVE_NORMALIZED_TO_0_1_M_DISPLAY_ONLY"
    ys = document["positions"][1::3]
    assert max(ys) - min(ys) == pytest.approx(0.1, abs=1e-6)


def test_wrong_inputs_are_rejected() -> None:
    with pytest.raises(ArPreviewError, match="cad_preview_required"):
        build_ar_preview_package(object())  # type: ignore[arg-type]


def test_swift_golden_literal_is_the_canonical_form_this_module_writes() -> None:
    # The iOS XCTest embeds a golden package; it must be byte-identical to this module's
    # canonicalisation so the phone's splice-and-hash digest check matches the writer.
    import re
    from pathlib import Path

    from packlab_core.ar_preview import _canonical

    swift = (
        Path(__file__).resolve().parents[2]
        / "apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift"
    ).read_text(encoding="utf-8")
    literal = re.search(r'static let golden = #"(.*?)"#', swift)
    assert literal is not None
    document = json.loads(literal.group(1))
    claimed = document.pop("content_sha256")
    assert hashlib.sha256(_canonical(document)).hexdigest() == claimed
    assert _canonical({**document, "content_sha256": claimed}).decode("ascii") == literal.group(1)


def _signed_volume(document: dict) -> float:
    p = document["positions"]
    points = [tuple(p[i : i + 3]) for i in range(0, len(p), 3)]
    total = 0.0
    idx = document["indices"]
    for i in range(0, len(idx), 3):
        a, b, c = (points[idx[i]], points[idx[i + 1]], points[idx[i + 2]])
        total += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )
    return total / 6.0


def test_frame_conversion_is_a_rotation_and_keeps_outward_winding() -> None:
    # Review P2-1: a mirrored axis map or reversed triangle winding flips the sign and
    # would render the one-sided material inside-out on the phone.
    preview = _preview()
    source_volume = _signed_volume(
        {
            "positions": [value * 0.001 for vertex in preview.mesh.vertices for value in vertex],
            "indices": [index for triangle in preview.mesh.triangles for index in triangle],
        }
    )
    document = json.loads(build_ar_preview_package(preview))
    volume = _signed_volume(document)
    assert source_volume > 0
    assert volume == pytest.approx(source_volume, rel=1e-3)


def _forged(preview, **changes):
    import copy

    forged = copy.copy(preview)
    for name, value in changes.items():
        object.__setattr__(forged, name, value)  # test-only forgery past __post_init__
    return forged


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"mold_use_authorized": True}, "preview_authority_invalid"),
        ({"physical_accuracy_validation_status": "VALIDATED"}, "preview_authority_invalid"),
        ({"authority_class": "SCAN_MASTER"}, "preview_authority_invalid"),
        ({"coordinate_unit": "mm"}, "preview_coordinate_unit_unsupported"),
    ],
)
def test_authority_and_unit_guards(changes: dict, code: str) -> None:
    # Review P2-2 / P3-5 / P3-6.
    with pytest.raises(ArPreviewError, match=code):
        build_ar_preview_package(_forged(_preview(), **changes))


def test_size_and_extent_guards() -> None:
    from packlab_core.geometry_adapter import TriangleMeshData

    preview = _preview()
    tiny = TriangleMeshData(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)), ())
    with pytest.raises(ArPreviewError, match="mesh_size_out_of_bounds"):
        build_ar_preview_package(_forged(preview, mesh=tiny))
    huge = TriangleMeshData(
        tuple((x * 1000.0, y * 1000.0, z * 1000.0) for x, y, z in preview.mesh.vertices),
        preview.mesh.triangles,
    )
    with pytest.raises(ArPreviewError, match="extent_exceeds_display_bound"):
        build_ar_preview_package(_forged(preview, mesh=huge))


def test_package_names_the_parent_authority_revision() -> None:
    preview = _preview()
    document = json.loads(build_ar_preview_package(preview))
    assert (
        document["source"]["parent_authority_revision_id"] == preview.parent_authority_revision_id
    )
