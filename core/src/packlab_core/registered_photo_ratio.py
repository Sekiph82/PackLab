"""Provenance-bound observation of COLMAP's registered-photo ratio."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .reconstruction import ReconstructionStageResult, RunStatus
from .sparse_mapping import (
    RegisteredImageStatistics,
    SparseMappingRequest,
    SparseMappingRun,
    normalize_sparse_mapping_result,
)

REGISTERED_PHOTO_RATIO_CONTRACT = "packlab.registered-photo-ratio.v1"


@dataclass(frozen=True, slots=True)
class RegisteredPhotoRatioReport:
    """Canonical observation report; it never decides reconstruction acceptance."""

    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return json.loads(json.dumps(self.payload, sort_keys=True, allow_nan=False))

    def serialize(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _invalid_report(code: str) -> RegisteredPhotoRatioReport:
    return RegisteredPhotoRatioReport(
        {
            "contract": REGISTERED_PHOTO_RATIO_CONTRACT,
            "observation_status": "invalid",
            "acceptance_status": "not_evaluated",
            "source_evidence": None,
            "statistics": None,
            "diagnostics": [{"code": code}],
        }
    )


def _validated_run(run: object) -> tuple[SparseMappingRun | None, str | None]:
    if not isinstance(run, SparseMappingRun):
        return None, "sparse_mapping_run_invalid"
    request = run.request
    stage = run.stage_result
    if not isinstance(request, SparseMappingRequest) or not isinstance(
        stage, ReconstructionStageResult
    ):
        return None, "sparse_mapping_run_invalid"
    if not isinstance(request.image_asset_ids, tuple) or not isinstance(stage.stdout, str):
        return None, "sparse_mapping_run_invalid"
    try:
        checked_request = SparseMappingRequest(
            image_asset_ids=tuple(request.image_asset_ids),
            source_revision=request.source_revision,
            source_digest=request.source_digest,
            matcher_selection_digest=request.matcher_selection_digest,
            configuration=request.configuration,
            engine_id=request.engine_id,
            engine_version=request.engine_version,
        )
        normalized = normalize_sparse_mapping_result(checked_request, stage)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None, "sparse_mapping_run_invalid"
    if run.status is not normalized.status:
        return None, "sparse_mapping_run_invalid"
    if run.status is RunStatus.SUCCEEDED:
        if (
            not isinstance(run.statistics, RegisteredImageStatistics)
            or run.statistics != normalized.statistics
            or run.sparse_model_asset_id != normalized.sparse_model_asset_id
        ):
            return None, "sparse_mapping_run_invalid"
    elif run.statistics is not None or run.sparse_model_asset_id is not None:
        return None, "sparse_mapping_run_invalid"
    return normalized, None


def build_registered_photo_ratio_report(run: object) -> RegisteredPhotoRatioReport:
    """Return observed COLMAP registration facts without applying an acceptance policy.

    The denominator binding is the digest of the ordered request image IDs, so
    reordering or changing even one input changes the report's source identity.
    Stage text is represented only by its digest; raw process output is omitted.
    """
    normalized, invalid_code = _validated_run(run)
    if normalized is None:
        return _invalid_report(invalid_code or "sparse_mapping_run_invalid")

    request = normalized.request
    stage = normalized.stage_result
    image_ids = list(request.image_asset_ids)
    image_ids_digest = _canonical_digest(image_ids)
    request_digest = request.request_digest()
    stdout_digest = hashlib.sha256(stage.stdout.encode("utf-8")).hexdigest()
    stage_evidence = {
        "engine_id": request.engine_id,
        "engine_version": request.engine_version,
        "request_sha256": request_digest,
        "stage_id": stage.stage_id,
        "stage_status": stage.status.value,
        "exit_code": stage.exit_code,
        "cancelled": stage.cancelled,
        "stdout_sha256": stdout_digest,
    }
    source_evidence: dict[str, object] = {
        "source_revision": request.source_revision,
        "source_sha256": request.source_digest,
        "matcher_selection_sha256": request.matcher_selection_digest,
        "ordered_input_photo_count": len(image_ids),
        "ordered_input_photo_ids_digest_algorithm": "sha256_canonical_json_ordered_string_array_v1",
        "ordered_input_photo_ids_sha256": image_ids_digest,
        "request_sha256": request_digest,
        "stage": stage_evidence,
        "stage_evidence_digest_algorithm": "sha256_canonical_json_v1",
        "stage_evidence_sha256": _canonical_digest(stage_evidence),
    }

    if normalized.status is not RunStatus.SUCCEEDED or normalized.statistics is None:
        return RegisteredPhotoRatioReport(
            {
                "contract": REGISTERED_PHOTO_RATIO_CONTRACT,
                "observation_status": "unavailable",
                "acceptance_status": "not_evaluated",
                "source_evidence": source_evidence,
                "statistics": None,
                "diagnostics": [{"code": "colmap_stage_not_successful"}],
            }
        )

    stats = normalized.statistics
    ratio = stats.registered_images / stats.total_images
    observation_code = (
        "registered_photo_ratio_zero"
        if stats.registered_images == 0
        else "registered_photo_ratio_observed"
    )
    return RegisteredPhotoRatioReport(
        {
            "contract": REGISTERED_PHOTO_RATIO_CONTRACT,
            "observation_status": "observed",
            "acceptance_status": "not_evaluated",
            "source_evidence": source_evidence,
            "statistics": {
                "total_input_photos": stats.total_images,
                "registered_photos": stats.registered_images,
                "unregistered_photos": stats.unregistered_images,
                "registration_ratio": ratio,
            },
            "diagnostics": [{"code": observation_code}],
        }
    )
