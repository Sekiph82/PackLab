"""Studio service seam for running and cancelling reconstruction jobs."""

from __future__ import annotations

from dataclasses import dataclass

from packlab_core.reconstruction import CancelToken, RunStatus
from packlab_core.reconstruction_orchestrator import (
    ReconstructionOrchestrationRequest,
    ReconstructionOrchestrationResult,
    ReconstructionOrchestrator,
)

from .jobs import JobManager
from .reconstruction_workspace import (
    ReconstructionWorkspace,
    ReconstructionWorkspaceManager,
)


@dataclass(frozen=True, slots=True)
class ReconstructionExecution:
    token: CancelToken
    result: ReconstructionOrchestrationResult


class ReconstructionExecutionService:
    """Bridge one logical Studio job to core orchestration and workspace state."""

    def __init__(
        self,
        jobs: JobManager,
        workspaces: ReconstructionWorkspaceManager,
        orchestrator: ReconstructionOrchestrator | None = None,
    ) -> None:
        self.jobs = jobs
        self.workspaces = workspaces
        self.orchestrator = orchestrator or ReconstructionOrchestrator()

    def execute(
        self,
        job_id: str,
        workspace: ReconstructionWorkspace,
        request: ReconstructionOrchestrationRequest,
        *,
        cancel: CancelToken | None = None,
    ) -> ReconstructionExecution:
        token = CancelToken() if cancel is None else cancel
        self.jobs.start(job_id)

        def request_cancel() -> bool:
            token.cancel()
            # The owned stage/process must normalize before the job becomes
            # terminal. The UI request therefore leaves the job CANCELLING.
            return False

        self.jobs.register_cancel_hook(job_id, request_cancel)
        result = self.orchestrator.run(request, token)
        if result.status is RunStatus.CANCELLED:
            self.workspaces.cancel(workspace, result.failure_reason or "reconstruction cancelled")
            self.jobs.finish_cancel(job_id)
        elif result.status is RunStatus.FAILED:
            self.workspaces.fail(workspace, result.failure_reason or "reconstruction failed")
            self.jobs.fail(job_id, result.failure_reason or "reconstruction failed")
        else:
            self.workspaces.complete(workspace, parameters=result.as_dict())
            self.jobs.succeed(job_id, "reconstruction completed")
        return ReconstructionExecution(token, result)


__all__ = ["ReconstructionExecution", "ReconstructionExecutionService"]
