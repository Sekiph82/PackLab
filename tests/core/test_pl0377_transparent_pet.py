"""PL-0377: transparent PET limitation behaviour on provenance-bearing synthetic fixtures.

Fixtures are the clear-PET samples of the public M17 golden subset (PackLab-generated
Blender renders and generated meshes; idealized shader, no measured optical behaviour).
The surface dropout applied to the mesh is a seeded, labelled SIMULATION of what
photogrammetry typically loses on clear PET. Nothing here is a physical optical test,
a factory sample or a measurement.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_object_surface_texture_qa import _qa, _render

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.geometry_statistics import compute_geometry_statistics
from packlab_core.reconstruction import ScaleState
from packlab_core.reconstruction_anomaly import detect_reconstruction_anomalies
from packlab_core.reconstruction_confidence import (
    RECONSTRUCTION_CONFIDENCE_CONTRACT,
    ReconstructionConfidenceReport,
)
from packlab_core.rescan_decision import decide_rescan

SUBSET = Path(__file__).resolve().parents[1] / "fixtures" / "m17_golden_subset"
CLEAR_PET = ("syn_jar_pet_clear_v02", "syn_sachet_pet_clear_v01")


def _sample(sample_id: str) -> dict:
    manifest = json.loads((SUBSET / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["fully_synthetic"] is True
    assert manifest["physical_measurements_present"] is False
    return next(item for item in manifest["samples"] if item["id"] == sample_id)


def _mesh(sample_id: str) -> TriangleMeshData:
    lines = (SUBSET / "ground_truth" / f"{sample_id}.ply").read_text(encoding="ascii").splitlines()
    header_end = lines.index("end_header")
    vertex_count = int(next(line.split()[2] for line in lines if line.startswith("element vertex")))
    body = lines[header_end + 1 :]
    vertices = tuple(tuple(float(v) for v in row.split()[:3]) for row in body[:vertex_count])
    triangles: list[tuple[int, int, int]] = []
    for row in body[vertex_count:]:
        values = [int(v) for v in row.split()]
        polygon = values[1 : 1 + values[0]]
        triangles.extend(
            (polygon[0], polygon[i], polygon[i + 1]) for i in range(1, len(polygon) - 1)
        )
    return TriangleMeshData(vertices, tuple(triangles))


def _simulated_transparency_dropout(mesh: TriangleMeshData) -> TriangleMeshData:
    """SIMULATED: drop faces of a camera-facing window (centroid on +x, mid height)."""
    zs = [vertex[2] for vertex in mesh.vertices]
    low, high = min(zs) + 0.2 * (max(zs) - min(zs)), min(zs) + 0.8 * (max(zs) - min(zs))

    def centroid(triangle: tuple[int, int, int]) -> tuple[float, float, float]:
        points = [mesh.vertices[index] for index in triangle]
        return tuple(sum(point[axis] for point in points) / 3.0 for axis in range(3))  # type: ignore[return-value]

    kept = tuple(
        triangle
        for triangle in mesh.triangles
        if not (centroid(triangle)[0] > 0.0 and low <= centroid(triangle)[2] <= high)
    )
    assert 0 < len(kept) < len(mesh.triangles)
    return TriangleMeshData(mesh.vertices, kept)


def _confidence() -> ReconstructionConfidenceReport:
    return ReconstructionConfidenceReport(
        {
            "contract": RECONSTRUCTION_CONFIDENCE_CONTRACT,
            "authority": "diagnostic_only_no_physical_accuracy_or_acceptance_claim",
            "observation_status": "observed",
            "threshold_status": "meets_profile",
            "acceptance_status": "not_evaluated",
        }
    )


@pytest.mark.parametrize("sample_id", CLEAR_PET)
def test_clear_pet_fixture_is_explicitly_simulated(sample_id: str) -> None:
    # Criterion 3: material and measurement authority remain simulated.
    sample = _sample(sample_id)
    material = sample["material_appearance"]
    assert material["finish"] == "pet_clear" and material["transmission_weight"] > 0
    assert "not measured" in material["warning"]
    assert sample["synthetic"] is True
    assert "no physical" in sample["measurement_authority"]


@pytest.mark.parametrize("sample_id", CLEAR_PET)
def test_clear_pet_render_triggers_the_low_texture_warning_and_never_proceeds(
    sample_id: str,
) -> None:
    # Criterion 1: a deterministic limitation path in existing consumers (QA + decision tree).
    png, samples, mask = _render(sample_id)
    first = _qa(png, samples, mask)
    assert first == _qa(png, samples, mask)
    texture = first["photos"][0]["object_surface_texture"]
    assert texture["status"] == "warning"
    assert texture["reason_code"] == "low_object_surface_texture"
    assert first["overall"]["status"] == "review_required"
    decision = decide_rescan(first)
    assert decision["primary_action"] != "proceed_to_reconstruction_review"
    assert "surface_treatment_review" in {item["action"] for item in decision["actions"]}


@pytest.mark.parametrize("sample_id", CLEAR_PET)
def test_incomplete_clear_pet_reconstruction_is_flagged_not_complete(sample_id: str) -> None:
    # Criterion 2: a reconstruction with a transparency dropout is reported as incomplete
    # review evidence and carries no physical authority.
    intact = _mesh(sample_id)
    intact_statistics = compute_geometry_statistics(
        intact, geometry_revision_id=f"intact-{sample_id}", scale_state=ScaleState.RELATIVE
    )
    # Control: the generated mesh is closed, so any boundary edge below comes from dropout.
    assert dict(intact_statistics.topology_indicators)["boundary_edge_count"] == 0
    holed = _simulated_transparency_dropout(intact)
    statistics = compute_geometry_statistics(
        holed,
        geometry_revision_id=f"simulated-dropout-{sample_id}",
        scale_state=ScaleState.RELATIVE,
    )
    report = detect_reconstruction_anomalies(statistics, _confidence())
    codes = {item.code for item in report.findings}
    assert report.status == "REVIEW_REQUIRED"
    assert "mesh_boundary_edges_present" in codes
    payload = report.as_dict()
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["mold_use_authorized"] is False
    assert payload["geometry_mutated"] is False
    assert statistics.scale_state is ScaleState.RELATIVE
