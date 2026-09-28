from __future__ import annotations

import hashlib
import sys
import threading

import pytest

from packlab_core.reconstruction import (
    BackendProvenance,
    CancelToken,
    ReconstructionBackendId,
    ReconstructionCapability,
    ReconstructionInputSet,
    ReconstructionJobSpec,
    ReconstructionStageResult,
    RunStatus,
    StageStatus,
)
from packlab_core.reconstruction_orchestrator import (
    STAGE_ORDER,
    ReconstructionOrchestrationError,
    ReconstructionOrchestrationRequest,
    ReconstructionOrchestrator,
    ReconstructionStageDefinition,
    ReconstructionStageExecution,
)
from packlab_core.reconstruction_process import run_reconstruction_stage


def _request(executors=None) -> ReconstructionOrchestrationRequest:
    source_digest = hashlib.sha256(b"raw").hexdigest()
    inputs = ReconstructionInputSet(
        "project-1",
        "raw/capture.packscan",
        "raw-revision-1",
        source_digest,
        ("working/reconstruction/r1/inputs/001.jpg", "working/reconstruction/r1/inputs/002.jpg"),
    )
    job = ReconstructionJobSpec(
        "job-1",
        "project-1",
        3,
        inputs,
        ReconstructionBackendId.COLMAP_OPENMVS,
        configuration={"preset": "cpu-safe-v1"},
        requested_capabilities=(
            ReconstructionCapability.SPARSE,
            ReconstructionCapability.DENSE,
            ReconstructionCapability.MESH,
            ReconstructionCapability.TEXTURE,
        ),
    )
    callbacks = executors or {}
    definitions = []
    for index, stage_id in enumerate(STAGE_ORDER):

        def execute(context, *, _stage_id=stage_id, _index=index):
            callback = callbacks.get(_stage_id)
            if callback is not None:
                return callback(context)
            return ReconstructionStageExecution(
                _stage_id,
                ReconstructionStageResult(_stage_id, StageStatus.SUCCEEDED, 0, 0.01),
                {"primary": f"working/reconstruction/r1/{_stage_id}/output"},
                outputs_verified=True,
                payload={"stage_index": _index},
            )

        definitions.append(
            ReconstructionStageDefinition(
                stage_id,
                execute,
                () if index == 0 else (STAGE_ORDER[index - 1],),
                configuration={"stage_version": "1"},
            )
        )
    return ReconstructionOrchestrationRequest(
        job,
        "working/reconstruction/r1",
        BackendProvenance(
            ReconstructionBackendId.COLMAP_OPENMVS, "3.12.6/2.4.0", "fixture", "external"
        ),
        tuple(definitions),
        configuration={"resource_policy": "cpu-safe-v1"},
    )


def test_ordered_success_publishes_one_manifest_with_all_stage_provenance() -> None:
    request = _request()
    result = ReconstructionOrchestrator().run(request)

    assert result.status is RunStatus.SUCCEEDED
    assert result.output is not None
    assert tuple(item.stage_id for item in result.stage_results) == STAGE_ORDER
    assert result.output.configuration_digest == request.configuration_digest
    assert len(result.output.asset_paths) == len(STAGE_ORDER)
    assert result.output.authority_class == "RECONSTRUCTION_OBSERVATION"
    assert result.output.scale_state.value == "relative"


def test_stage_failure_stops_downstream_and_never_exposes_partial_success() -> None:
    called: list[str] = []

    def fail(context):
        called.append(context.previous[-1].stage_id)
        return ReconstructionStageExecution(
            "dense-point-cloud",
            ReconstructionStageResult(
                "dense-point-cloud", StageStatus.FAILED, 7, 0.02, failure_reason="engine failed"
            ),
        )

    request = _request({"dense-point-cloud": fail})
    result = ReconstructionOrchestrator().run(request)

    assert result.status is RunStatus.FAILED
    assert result.output is None
    assert [item.stage_id for item in result.stage_results] == [
        "feature-extraction",
        "matching",
        "sparse-mapping",
        "openmvs-conversion",
        "dense-point-cloud",
    ]
    assert called == ["openmvs-conversion"]


def test_missing_verified_output_is_fail_closed() -> None:
    def missing(_context):
        return ReconstructionStageExecution(
            "matching", ReconstructionStageResult("matching", StageStatus.SUCCEEDED, 0, 0.01)
        )

    result = ReconstructionOrchestrator().run(_request({"matching": missing}))

    assert result.status is RunStatus.FAILED
    assert result.output is None
    assert "verify" in (result.failure_reason or "")
    assert [item.stage_id for item in result.stage_results] == ["feature-extraction", "matching"]


def test_cancel_before_start_and_completion_race_are_recoverable() -> None:
    token = CancelToken()
    token.cancel()
    cancelled = ReconstructionOrchestrator().run(_request(), token)
    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.output is None
    assert cancelled.stage_results[0].status is StageStatus.CANCELLED

    race_token = CancelToken()

    def cancel_after_stage(context):
        race_token.cancel()
        return ReconstructionStageExecution(
            "matching",
            ReconstructionStageResult("matching", StageStatus.SUCCEEDED, 0, 0.01),
            {"primary": "working/reconstruction/r1/matching/output"},
            outputs_verified=True,
        )

    raced = ReconstructionOrchestrator().run(_request({"matching": cancel_after_stage}), race_token)
    assert raced.status is RunStatus.CANCELLED
    assert raced.output is None
    assert raced.stage_results[-1].cancelled is True


def test_cancel_token_stops_owned_process_and_repeated_cancel_is_idempotent() -> None:
    token = CancelToken()
    started = threading.Event()
    holder = {}

    def blocking(context):
        started.set()
        stage = run_reconstruction_stage(
            "feature-extraction",
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cancel_event=context.cancel.event,
        )
        holder["stage"] = stage
        return ReconstructionStageExecution("feature-extraction", stage)

    thread = threading.Thread(
        target=lambda: holder.setdefault(
            "result",
            ReconstructionOrchestrator().run(_request({"feature-extraction": blocking}), token),
        ),
        daemon=True,
    )
    thread.start()
    assert started.wait(timeout=2.0)
    token.cancel()
    token.cancel()
    thread.join(timeout=4.0)

    assert not thread.is_alive()
    result = holder["result"]
    assert result.status is RunStatus.CANCELLED
    assert result.output is None
    assert holder["stage"].status is StageStatus.CANCELLED


def test_order_and_dependency_contract_rejects_invalid_plan() -> None:
    request = _request()
    definitions = list(request.stages)
    definitions[1] = ReconstructionStageDefinition(
        "matching", definitions[1].execute, dependencies=("feature-extraction", "unexpected")
    )
    with pytest.raises(ReconstructionOrchestrationError, match="invalid dependencies"):
        ReconstructionOrchestrationRequest(
            request.job,
            request.workspace,
            request.backend_provenance,
            tuple(definitions),
        )


def test_configuration_digest_is_stable_and_changes_with_stage_configuration() -> None:
    first = _request()
    second = _request()
    assert first.configuration_digest == second.configuration_digest
    changed = list(second.stages)
    changed[0] = ReconstructionStageDefinition(
        changed[0].stage_id,
        changed[0].execute,
        changed[0].dependencies,
        configuration={"stage_version": "2"},
    )
    third = ReconstructionOrchestrationRequest(
        second.job,
        second.workspace,
        second.backend_provenance,
        tuple(changed),
        second.configuration,
    )
    assert third.configuration_digest != first.configuration_digest
