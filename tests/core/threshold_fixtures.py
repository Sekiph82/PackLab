"""Shared synthetic fixtures for PL-0221/PL-0224 tests (software math only, never physical)."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping, Sequence

from packlab_core.acceptance_thresholds import (
    BenchmarkMeasurementObservation,
    OwnerThresholdAcceptance,
)
from packlab_core.design_model import (
    DesignModelParameter,
    DesignModelRevision,
    PackageFamily,
    create_design_model_revision,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.physical_accuracy_benchmark import (
    REQUIRED_BENCHMARK_CATEGORIES,
    BenchmarkEnvironment,
    CaliperGroundTruth,
    PhysicalAccuracyBenchmarkRecord,
    PhysicalBenchmarkSample,
)
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.visual_material_library import MaterialFamily

MATERIAL = {
    "matte_bottle": MaterialFamily.HDPE,
    "glossy_bottle": MaterialFamily.PET,
    "jerrycan": MaterialFamily.HDPE,
}
NOW = "2026-11-19T00:00:00Z"
PROJECT_ID = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), ((0, 1, 2),))


def benchmark_fixture(
    *,
    per_category: int = 10,
    evidence_kind: str = "SYNTHETIC",
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    seed: int = 221,
    errors: Mapping[str, Sequence[float]] | None = None,
    uncertainty_mm: Mapping[str, float] | None = None,
) -> tuple[PhysicalAccuracyBenchmarkRecord, list[BenchmarkMeasurementObservation]]:
    """Seeded synthetic record: caliper truth 100..200 mm, error ~ N(0.1, 0.2) mm unless given."""

    rng = random.Random(seed)
    samples: list[PhysicalBenchmarkSample] = []
    observations: list[BenchmarkMeasurementObservation] = []
    for category in REQUIRED_BENCHMARK_CATEGORIES:
        chosen = (errors or {}).get(category)
        count = len(chosen) if chosen is not None else per_category
        u = (uncertainty_mm or {}).get(category, 0.02)
        for index in range(count):
            tag = f"{category.upper()}-{index:03d}"
            truth = round(rng.uniform(100.0, 200.0), 2)
            error = chosen[index] if chosen is not None else rng.gauss(0.1, 0.2)
            samples.append(
                PhysicalBenchmarkSample(
                    f"SAMPLE-{tag}",
                    category,
                    "ACCEPTED",
                    f"scan-{tag}",
                    "scan-rev-1",
                    f"meas-{tag}",
                    "meas-rev-1",
                    "ref:synthetic-evidence",
                    CaliperGroundTruth(
                        f"gt-{tag}",
                        f"dim-{tag}",
                        truth,
                        (truth, truth),
                        u,
                        "ref:synthetic-caliper",
                        "ref:synthetic-cal",
                        "ref:synthetic-owner",
                        NOW,
                    ),
                    None,
                )
            )
            observations.append(
                BenchmarkMeasurementObservation(
                    "BENCH-SYNTHETIC-0221",
                    f"SAMPLE-{tag}",
                    f"meas-{tag}",
                    "meas-rev-1",
                    f"dim-{tag}",
                    "overall_height",
                    MATERIAL[category],
                    truth + error,
                    scale_state,
                    "scale-prov-1" if scale_state is ScaleState.METRIC_VERIFIED else None,
                    evidence_kind,
                )
            )
    record = PhysicalAccuracyBenchmarkRecord(
        "BENCH-SYNTHETIC-0221",
        "READY_FOR_AUDIT",
        "ref:synthetic-operator",
        NOW,
        BenchmarkEnvironment(21.0, 50.0, "diffuse", "mat", "turntable", "synthetic", "synthetic"),
        tuple(samples),
    )
    return record, observations


def owner_acceptance(proposal: Mapping[str, object]) -> OwnerThresholdAcceptance:
    return OwnerThresholdAcceptance(str(proposal["proposal_sha256"]), "ref:owner", NOW, "reviewed")


def scan_master(
    *,
    scale_state: ScaleState = ScaleState.METRIC_VERIFIED,
    validation_status: str | None = "OWNER_PHYSICAL_VALIDATION_ACCEPTED",
    coverage_gaps: tuple[str, ...] = (),
    authority_class: str = "SCAN_MASTER",
    revision_id: str | None = None,
    scale_provenance_id: str = "scale-provenance:pl0224-fixture",
    extra: Mapping[str, object] | None = None,
) -> ScanMasterRevision:
    """Hand-built test Scan Master. promote_scan_master forbids METRIC_VERIFIED and always
    writes DEFERRED_OWNER_VALIDATION; this fixture fakes the owner-only accepted status."""

    scan_id = revision_id or (
        f"scan-master:{hashlib.sha256(scale_state.value.encode()).hexdigest()}"
    )
    manifest: dict[str, object] = {
        "scan_master_revision_id": scan_id,
        "project_id": PROJECT_ID,
        "authority_class": authority_class,
        "output_geometry_sha256": mesh_sha256(MESH),
        "reconstruction_revision_id": "reconstruction:pl0224-fixture",
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": validation_status,
        "mold_use_authorized": False,
        "coverage_gaps": list(coverage_gaps),
    }
    if validation_status is None:
        del manifest["physical_accuracy_validation_status"]
    manifest.update(extra or {})
    return ScanMasterRevision(scan_id, PROJECT_ID, MESH, manifest)


def design_model(
    scan: ScanMasterRevision,
    family: PackageFamily = PackageFamily.BOTTLE,
    parameters: tuple[DesignModelParameter, ...] = (),
) -> DesignModelRevision:
    parent = bind_design_model_parent(
        scan, actor_id="operator-1", reason="PL-0224 fixture binding.", created_at_utc=NOW
    )
    return create_design_model_revision(
        parent,
        package_family=family,
        parameters=parameters,
        actor_id="operator-1",
        reason="PL-0224 fixture.",
        created_at_utc=NOW,
    )
