"""Build model: run one imported scan through the COLMAP/OpenMVS lane in the background.

The heavy work runs on a worker thread. Every JobManager call is marshalled back to
the Qt main thread, so job state keeps a single writer. Reconstruction itself goes
through the existing ReconstructionExecutionService -> ReconstructionOrchestrator,
inside a project-scoped ReconstructionWorkspace whose source is the RAW_CAPTURE.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import struct
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Protocol, cast

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from packlab_core.reconstruction import (
    BackendProvenance,
    CancelToken,
    ReconstructionBackendId,
    ReconstructionCapability,
    ReconstructionJobSpec,
    ReconstructionStageResult,
    RunStatus,
    StageStatus,
)
from packlab_core.reconstruction_orchestrator import (
    STAGE_ORDER,
    ReconstructionOrchestrationRequest,
    ReconstructionStageContext,
    ReconstructionStageDefinition,
    ReconstructionStageExecution,
)
from packlab_core.reconstruction_process import run_reconstruction_stage

from .engine_config import DiscoveryStatus, discover_engines
from .jobs import TERMINAL_STATES, JobManager, JobState
from .project import ProjectManager
from .reconstruction_execution import ReconstructionExecutionService
from .reconstruction_workspace import ReconstructionWorkspace, ReconstructionWorkspaceManager

BUILD_PRESET = "studio-cpu-v1"
MAX_IMAGE_SIZE = 2000  # long side; keeps CPU-only laptops at minutes, not hours
HEIC_SUFFIXES = {".heic", ".heif"}
COPY_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
# The command plan uses COLMAP 4.x option names (FeatureExtraction.*, FeatureMatching.*);
# 4.2.1 is the version it was verified with (Test-333) and the one PL-0444 bundles.
SUPPORTED_COLMAP_VERSIONS = ("4.2.1",)
# PL-0463 reproducibility: fixed COLMAP seeds (RANSAC + mapper sampling), single-threaded
# feature extraction (COLMAP 4.2.1 numbers images in completion order otherwise; measured
# +25 s on Test-333, then keypoints and descriptors are bit-identical), a single-threaded
# mapper (threaded bundle adjustment sums in a varying order) and sorted image order.
# Not fixed, documented instead: CPU matching uses an approximate (FAISS) index whose matches
# differ run to run (the exact brute-force matcher took 704 s instead of 38 s), and OpenMVS
# 2.4.0 has no seed option (densify of one identical scene gave 167,891 vs 168,892 points).
RANDOM_SEED = 0
EXTRACTION_THREADS = 1
MAPPER_THREADS = 1
OPENMVS_THREADS = 0  # 0 = all cores
DETERMINISM: dict[str, object] = {
    "colmap_random_seed": RANDOM_SEED,
    "colmap_extraction_threads": EXTRACTION_THREADS,
    "colmap_mapper_threads": MAPPER_THREADS,
    "openmvs_max_threads": OPENMVS_THREADS,
    "image_order": "sorted_working_name",
}
_COLMAP_VERSION = re.compile(r"COLMAP (\d+\.\d+\.\d+)")


def heic_decode_command(ffmpeg: Path, source: Path, target: Path) -> tuple[str, ...]:
    """Decode one untrusted HEIC photo: forced HEIF/MOV demuxer, local files only, no stdin."""
    return (
        str(ffmpeg),
        "-nostdin",
        "-v",
        "error",
        "-protocol_whitelist",
        "file",
        "-f",
        "mov",
        "-i",
        str(source),
        "-q:v",
        "2",
        "-y",
        str(target),
    )


def working_image_name(source: Path) -> str:
    """HEIC decodes keep the full source name (IMG_1.HEIC -> IMG_1.HEIC.jpg), so they
    can never collide with a JPEG of the same stem in the same capture."""
    return source.name + ".jpg" if source.suffix.lower() in HEIC_SUFFIXES else source.name


def find_ffmpeg() -> Path | None:
    """PACKLAB_FFMPEG_PATH, else absolute PATH entries only (never the current directory)."""
    configured = os.environ.get("PACKLAB_FFMPEG_PATH")
    if configured:
        return Path(configured)
    name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(entry) / name
        if Path(entry).is_absolute() and candidate.is_file():
            return candidate
    return None


STAGE_LABELS = {
    "feature-extraction": "Decoding photos and finding features",
    "matching": "Matching photos",
    "sparse-mapping": "Solving camera positions",
    "openmvs-conversion": "Preparing the dense scene",
    "dense-point-cloud": "Building the dense point cloud",
    "mesh-reconstruction": "Building the mesh",
    "mesh-refinement": "Refining the mesh",
    "texture-mesh": "Texturing the mesh",
}
NEXT_STEPS = (
    "Next: object-only cleanup (Mask Correction), scale and measure, Design Model "
    "(Editor), labels, export (Exports). The model is RECONSTRUCTION_OBSERVATION in "
    "relative units until scale is verified; it is not Scan Master."
)


class BuildModelError(RuntimeError):
    pass


# ---------------------------------------------------------------- main-thread marshalling


class _Call:
    def __init__(self, function: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]):
        self.function, self.args, self.kwargs = function, args, kwargs
        self.value: Any = None
        self.error: BaseException | None = None

    def run(self) -> None:
        try:
            self.value = self.function(*self.args, **self.kwargs)
        except BaseException as error:  # re-raised on the calling thread
            self.error = error


class MainThreadInvoker(QObject):
    """Runs callables on the thread that created it and waits for the result."""

    _invoke = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._owner = threading.get_ident()
        self._invoke.connect(self._run, Qt.ConnectionType.BlockingQueuedConnection)

    def _run(self, call: _Call) -> None:
        call.run()

    def call(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        box = _Call(function, args, kwargs)
        if threading.get_ident() == self._owner:
            box.run()
        else:
            self._invoke.emit(box)
        if box.error is not None:
            raise box.error
        return box.value


class _MainThreadJobs:
    """JobManager facade for worker threads; each call executes on the UI thread."""

    def __init__(self, jobs: JobManager, invoker: MainThreadInvoker) -> None:
        self._jobs = jobs
        self._invoker = invoker

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._jobs, name)
        return lambda *args, **kwargs: self._invoker.call(target, *args, **kwargs)


# ---------------------------------------------------------------------- engine backend


class BuildBackend(Protocol):
    """Supplies engine provenance and the eight orchestrator stages for one workspace."""

    def provenance(self, workspace_dir: Path) -> BackendProvenance: ...

    def stages(
        self, workspace_dir: Path, workspace_asset: str, facts: dict[str, object]
    ) -> tuple[ReconstructionStageDefinition, ...]: ...


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _registered_images(model: Path) -> int:
    """COLMAP images.bin starts with the uint64 count of registered images."""
    with (model / "images.bin").open("rb") as handle:
        return int(struct.unpack("<Q", handle.read(8))[0])


def _run_commands(
    stage_id: str,
    commands: Sequence[tuple[Sequence[str], Path]],
    cancel: CancelToken,
) -> ReconstructionStageResult:
    """Run commands in order; the first non-success ends the stage."""
    total = 0.0
    stdout: list[str] = []
    stderr: list[str] = []
    for args, cwd in commands:
        result = run_reconstruction_stage(stage_id, args, cancel_event=cancel.event, cwd=cwd)
        total += result.duration_seconds
        stdout.append(result.stdout)
        stderr.append(result.stderr)
        if result.status is not StageStatus.SUCCEEDED:
            return replace(result, duration_seconds=total)
    return ReconstructionStageResult(
        stage_id,
        StageStatus.SUCCEEDED,
        0,
        total,
        "".join(stdout)[-16_384:],
        "".join(stderr)[-16_384:],
    )


@dataclass(frozen=True, slots=True)
class ColmapOpenMvsBackend:
    """The CPU-safe COLMAP -> OpenMVS command plan proven on the owner's Test-333 scan."""

    colmap: Path
    openmvs: dict[str, Path]
    ffmpeg: Path | None = None

    @classmethod
    def discover(cls) -> ColmapOpenMvsBackend:
        report = discover_engines()
        usable = {DiscoveryStatus.CONFIGURED, DiscoveryStatus.PATH}
        missing = [
            record.engine_id
            for record in report.records
            if record.status not in usable or record.executable is None
        ]
        if missing:
            raise BuildModelError(
                "Reconstruction engines not found: "
                + ", ".join(missing)
                + ". Place them in the bundled engines folder or set PACKLAB_COLMAP_PATH"
                " and PACKLAB_OPENMVS_ROOT (see Settings > Reconstruction engines)."
            )
        paths = {record.engine_id: cast(Path, record.executable) for record in report.records}
        ffmpeg = find_ffmpeg()
        return cls(
            paths["colmap"],
            {
                key.removeprefix("openmvs."): value
                for key, value in paths.items()
                if key != "colmap"
            },
            ffmpeg,
        )

    def provenance(self, workspace_dir: Path) -> BackendProvenance:
        logs = workspace_dir / "logs"
        colmap = run_reconstruction_stage("engine-probe", (str(self.colmap), "help"), cwd=logs)
        openmvs = run_reconstruction_stage(
            "engine-probe", (str(self.openmvs["interface_colmap"]), "--help"), cwd=logs
        )
        colmap_version = next(iter(colmap.stdout.splitlines()), "COLMAP unknown").strip()
        found = _COLMAP_VERSION.search(colmap.stdout)
        if found is None or found.group(1) not in SUPPORTED_COLMAP_VERSIONS:
            raise BuildModelError(
                f"COLMAP {found.group(1) if found else 'version unknown'} is not supported by "
                f"the Build model plan (needs COLMAP {', '.join(SUPPORTED_COLMAP_VERSIONS)})"
            )
        # Without a console OpenMVS writes its banner only to a log in its working folder.
        banner = (
            openmvs.stdout
            + openmvs.stderr
            + "".join(
                log.read_text(encoding="utf-8", errors="replace")
                for log in sorted(logs.glob("InterfaceCOLMAP*.log"))
            )
        )
        match = re.search(r"OpenMVS \S+ (v[\w.]+)", banner)
        executables = {"colmap": self.colmap, **self.openmvs}
        version = f"{colmap_version[:80]}; OpenMVS {match.group(1) if match else 'unknown'}"
        if self.ffmpeg is not None:
            ffmpeg = run_reconstruction_stage(
                "engine-probe", (str(self.ffmpeg), "-nostdin", "-version"), cwd=logs
            )
            ffmpeg_version = next(iter(ffmpeg.stdout.splitlines()), "ffmpeg unknown")
            version += f"; HEIC decode {ffmpeg_version.split(' Copyright')[0].strip()[:80]}"
            executables["ffmpeg"] = self.ffmpeg
        return BackendProvenance(
            ReconstructionBackendId.COLMAP_OPENMVS,
            version,
            "local external executables (CPU)",
            "COLMAP BSD-3-Clause; OpenMVS AGPL-3.0 (external process, not bundled)",
            {name: _sha256_file(path) for name, path in sorted(executables.items())},
        )

    def stages(
        self, workspace_dir: Path, workspace_asset: str, facts: dict[str, object]
    ) -> tuple[ReconstructionStageDefinition, ...]:
        w = workspace_dir
        out = w / "outputs"
        images, database, sparse = (
            out / "colmap/images",
            out / "colmap/database.db",
            out / "colmap/sparse",
        )
        mvs = out / "mvs"
        colmap = str(self.colmap)
        tool = {key: str(value) for key, value in self.openmvs.items()}

        def asset(path: Path) -> str:
            return f"{workspace_asset}/{path.relative_to(w).as_posix()}"

        def require(*paths: Path) -> None:
            for path in paths:
                if not path.exists() or (path.is_file() and path.stat().st_size == 0):
                    raise BuildModelError(
                        f"expected output missing: {path.relative_to(w).as_posix()}"
                    )

        def done(
            stage_id: str, result: ReconstructionStageResult, outputs: dict[str, Path]
        ) -> ReconstructionStageExecution:
            if result.status is StageStatus.SUCCEEDED:
                require(*outputs.values())
            return ReconstructionStageExecution(
                stage_id,
                result,
                {name: asset(path) for name, path in outputs.items()},
                outputs_verified=result.status is StageStatus.SUCCEEDED,
            )

        def features(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            images.mkdir(parents=True, exist_ok=True)
            commands: list[tuple[Sequence[str], Path]] = []
            sources = sorted(
                (
                    w / Path(item).relative_to(workspace_asset)
                    for item in context.job.inputs.image_asset_ids
                ),
                key=working_image_name,
            )
            for source in sources:
                suffix = source.suffix.lower()
                if suffix in HEIC_SUFFIXES:
                    if self.ffmpeg is None:
                        raise BuildModelError("HEIC photos need ffmpeg; set PACKLAB_FFMPEG_PATH")
                    target = images / working_image_name(source)
                    commands.append((heic_decode_command(self.ffmpeg, source, target), w))
                elif suffix in COPY_SUFFIXES:
                    shutil.copyfile(source, images / working_image_name(source))
                else:
                    raise BuildModelError(f"unsupported photo type: {source.name}")
            facts["input_images"] = len(sources)
            commands.append(
                (
                    (
                        colmap,
                        "feature_extractor",
                        "--database_path",
                        str(database),
                        "--image_path",
                        str(images),
                        "--ImageReader.single_camera",
                        "1",
                        "--ImageReader.camera_model",
                        "OPENCV",
                        "--FeatureExtraction.use_gpu",
                        "0",
                        "--FeatureExtraction.max_image_size",
                        str(MAX_IMAGE_SIZE),
                        "--default_random_seed",
                        str(RANDOM_SEED),
                        "--FeatureExtraction.num_threads",
                        str(EXTRACTION_THREADS),
                    ),
                    w,
                )
            )
            # ponytail: photos decode one at a time; parallelize if decode dominates.
            result = _run_commands("feature-extraction", commands, context.cancel)
            return done("feature-extraction", result, {"database": database, "images": images})

        def matching(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            result = _run_commands(
                "matching",
                [
                    (
                        (
                            colmap,
                            "exhaustive_matcher",
                            "--database_path",
                            str(database),
                            "--FeatureMatching.use_gpu",
                            "0",
                            "--default_random_seed",
                            str(RANDOM_SEED),
                            "--TwoViewGeometry.random_seed",
                            str(RANDOM_SEED),
                        ),
                        w,
                    )
                ],
                context.cancel,
            )
            return done("matching", result, {"database": database})

        def mapping(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            sparse.mkdir(parents=True, exist_ok=True)
            result = _run_commands(
                "sparse-mapping",
                [
                    (
                        (
                            colmap,
                            "mapper",
                            "--database_path",
                            str(database),
                            "--image_path",
                            str(images),
                            "--output_path",
                            str(sparse),
                            "--default_random_seed",
                            str(RANDOM_SEED),
                            "--Mapper.random_seed",
                            str(RANDOM_SEED),
                            "--Mapper.num_threads",
                            str(MAPPER_THREADS),
                        ),
                        w,
                    )
                ],
                context.cancel,
            )
            if result.status is not StageStatus.SUCCEEDED:
                return done("sparse-mapping", result, {})
            models = [path for path in sparse.iterdir() if (path / "images.bin").is_file()]
            if not models:
                raise BuildModelError(
                    "camera solving registered no photos; retake with more overlap"
                )
            best = max(models, key=_registered_images)
            facts["sparse_model"] = best
            facts["registered_images"] = _registered_images(best)
            return done("sparse-mapping", result, {"model": best})

        def conversion(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            model = cast(Path, facts["sparse_model"])
            dense = out / "dense"
            mvs.mkdir(parents=True, exist_ok=True)
            result = _run_commands(
                "openmvs-conversion",
                [
                    (
                        (
                            colmap,
                            "image_undistorter",
                            "--image_path",
                            str(images),
                            "--input_path",
                            str(model),
                            "--output_path",
                            str(dense),
                            "--output_type",
                            "COLMAP",
                            "--max_image_size",
                            str(MAX_IMAGE_SIZE),
                        ),
                        w,
                    ),
                    (
                        (
                            tool["interface_colmap"],
                            "-i",
                            "../dense",
                            "-o",
                            "scene.mvs",
                            "--image-folder",
                            "../dense/images",
                        ),
                        mvs,
                    ),
                ],
                context.cancel,
            )
            return done("openmvs-conversion", result, {"scene": mvs / "scene.mvs"})

        def densify(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            result = _run_commands(
                "dense-point-cloud",
                [
                    (
                        (
                            tool["densify_point_cloud"],
                            "scene.mvs",
                            "--resolution-level",
                            "1",
                            "--max-threads",
                            str(OPENMVS_THREADS),
                        ),
                        mvs,
                    )
                ],
                context.cancel,
            )
            return done(
                "dense-point-cloud",
                result,
                {"scene": mvs / "scene_dense.mvs", "point_cloud": mvs / "scene_dense.ply"},
            )

        def mesh(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            result = _run_commands(
                "mesh-reconstruction",
                [((tool["reconstruct_mesh"], "scene_dense.mvs", "-p", "scene_dense.ply"), mvs)],
                context.cancel,
            )
            return done("mesh-reconstruction", result, {"mesh": mvs / "scene_dense_mesh.ply"})

        def refine(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            # Light CPU preset (~2 min on Test-333): one scale at quarter resolution.
            result = _run_commands(
                "mesh-refinement",
                [
                    (
                        (
                            tool["refine_mesh"],
                            "scene_dense.mvs",
                            "-m",
                            "scene_dense_mesh.ply",
                            "-o",
                            "scene_refined.mvs",
                            "--resolution-level",
                            "2",
                            "--scales",
                            "1",
                            "--max-threads",
                            str(OPENMVS_THREADS),
                        ),
                        mvs,
                    )
                ],
                context.cancel,
            )
            return done("mesh-refinement", result, {"mesh": mvs / "scene_refined.ply"})

        def texture(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            result = _run_commands(
                "texture-mesh",
                [
                    (
                        (
                            tool["texture_mesh"],
                            "scene_dense.mvs",
                            "-m",
                            "scene_refined.ply",
                            "-o",
                            "scene_textured.mvs",
                            "--export-type",
                            "obj",
                        ),
                        mvs,
                    )
                ],
                context.cancel,
            )
            return done("texture-mesh", result, {"textured_mesh": mvs / "scene_textured.obj"})

        executors = (features, matching, mapping, conversion, densify, mesh, refine, texture)
        return _definitions(
            executors, {"preset": BUILD_PRESET, "max_image_size": MAX_IMAGE_SIZE, **DETERMINISM}
        )


def _definitions(
    executors: Sequence[Callable[[ReconstructionStageContext], ReconstructionStageExecution]],
    configuration: dict[str, object],
) -> tuple[ReconstructionStageDefinition, ...]:
    return tuple(
        ReconstructionStageDefinition(
            stage_id,
            execute,
            () if index == 0 else (STAGE_ORDER[index - 1],),
            configuration=configuration,
        )
        for index, (stage_id, execute) in enumerate(zip(STAGE_ORDER, executors, strict=True))
    )


# ------------------------------------------------------------------------- controller


@dataclass(frozen=True, slots=True)
class BuildResult:
    job_id: str
    capture_id: str
    status: str  # succeeded | failed | cancelled
    message: str
    model_path: Path | None = None
    textured_mesh_path: Path | None = None
    registered_images: int | None = None
    input_images: int | None = None
    seconds: float = 0.0
    workspace_dir: Path | None = None
    facts: dict[str, object] = field(default_factory=dict)


def register_raw_capture(project: ProjectManager, package: Path, package_sha256: str) -> str:
    """Copy an imported package into the open project's RAW_CAPTURE area (idempotent)."""
    if project.layout is None:
        raise BuildModelError("no project is open")
    if not re.fullmatch(r"[0-9a-f]{64}", package_sha256):
        raise BuildModelError("package digest is invalid")
    relative = f"captures/{package_sha256}.packscan"
    target = project.layout.path("raw", relative)
    if not target.is_file() or _sha256_file(target) != package_sha256:
        if _sha256_file(package) != package_sha256:
            raise BuildModelError("imported package changed since import")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copyfile(package, staging)
            os.replace(staging, target)
        finally:
            staging.unlink(missing_ok=True)
    return f"raw/{relative}"


class BuildModelController(QObject):
    """Queues one background build per request and reports through JobManager."""

    build_started = Signal(str, str)  # job_id, capture_id
    build_finished = Signal(object)  # BuildResult

    def __init__(
        self,
        jobs: JobManager,
        projects: ProjectManager,
        *,
        backend: BuildBackend | None = None,
    ) -> None:
        super().__init__()
        self.jobs = jobs
        self.projects = projects
        self._backend = backend
        self._invoker = MainThreadInvoker()
        # ponytail: one build at a time (CPU-bound engines); FIFO of not-yet-started runs.
        self._queue: list[tuple[str, threading.Thread]] = []
        self._running: str | None = None
        self._by_package: dict[str, str] = {}  # package sha256 -> latest job id
        self.build_finished.connect(self._on_finished)

    def build(self, package: Path, capture_id: str, package_sha256: str) -> str:
        """Register the capture in the open project and start a background build."""
        if self.projects.layout is None or self.projects.metadata is None:
            raise BuildModelError("open a project before building a model")
        existing = self._by_package.get(package_sha256)
        if existing is not None and self.jobs.get(existing).state not in TERMINAL_STATES:
            return existing  # already queued or running for this scan
        backend = self._backend or ColmapOpenMvsBackend.discover()
        source_asset = register_raw_capture(self.projects, package, package_sha256)
        job = self.jobs.create(f"Build model {capture_id[:8]}", "reconstruction")
        token = CancelToken()

        def cancel_hook() -> bool:
            token.cancel()
            return False

        self.jobs.register_cancel_hook(job.job_id, cancel_hook)
        layout = self.projects.layout
        metadata = self.projects.metadata
        thread = threading.Thread(
            target=self._work,
            args=(
                job.job_id,
                capture_id,
                backend,
                layout,
                metadata,
                source_asset,
                package_sha256,
                token,
            ),
            name=f"packlab-build-{job.job_id[:8]}",
            daemon=True,
        )
        self._by_package[package_sha256] = job.job_id
        self._queue.append((job.job_id, thread))
        self.build_started.emit(job.job_id, capture_id)
        self._start_next()
        return job.job_id

    def _start_next(self) -> None:
        if self._running is None and self._queue:
            self._running, thread = self._queue.pop(0)
            thread.start()

    def _on_finished(self, result: BuildResult) -> None:
        if result.job_id == self._running:
            self._running = None
        self._start_next()

    def _work(
        self,
        job_id: str,
        capture_id: str,
        backend: BuildBackend,
        layout: Any,
        metadata: Any,
        source_asset: str,
        package_sha256: str,
        token: CancelToken,
    ) -> None:
        started = time.monotonic()
        jobs = cast(JobManager, _MainThreadJobs(self.jobs, self._invoker))
        workspaces = ReconstructionWorkspaceManager(layout)
        workspace: ReconstructionWorkspace | None = None
        facts: dict[str, object] = {}

        def cancelled() -> bool:
            # A queued job is cancelled by JobManager without calling the hook.
            return token.cancelled or jobs.get(job_id).state is JobState.CANCELLED

        def finish(status: str, message: str, **extra: Any) -> None:
            self._invoker.call(
                self.build_finished.emit,
                BuildResult(
                    job_id,
                    capture_id,
                    status,
                    message,
                    registered_images=cast(int | None, facts.get("registered_images")),
                    input_images=cast(int | None, facts.get("input_images")),
                    seconds=time.monotonic() - started,
                    workspace_dir=None if workspace is None else workspace.path,
                    facts=dict(facts),
                    **extra,
                ),
            )

        try:
            workspace = workspaces.create(
                project_id=metadata.project_id,
                project_revision=metadata.revision,
                source_asset_id=source_asset,
                source_digest=package_sha256,
            )
            working_set = workspaces.materialize_working_set(workspace)
            if cancelled():
                workspaces.cancel(workspace, "cancelled before start")
                jobs.finish_cancel(job_id)
                finish("cancelled", "Build cancelled.")
                return
            provenance = backend.provenance(workspace.path)
            definitions = backend.stages(workspace.path, workspace.relative_path, facts)
            total = len(definitions)

            def with_progress(
                index: int, definition: ReconstructionStageDefinition
            ) -> ReconstructionStageDefinition:
                def execute(context: ReconstructionStageContext) -> ReconstructionStageExecution:
                    label = STAGE_LABELS.get(definition.stage_id, definition.stage_id)
                    jobs.update_progress(job_id, index / total, f"{index + 1}/{total} {label}")
                    return definition.execute(context)

                return replace(definition, execute=execute)

            stages = tuple(with_progress(index, item) for index, item in enumerate(definitions))
            request = ReconstructionOrchestrationRequest(
                ReconstructionJobSpec(
                    job_id,
                    metadata.project_id,
                    metadata.revision,
                    working_set.inputs,
                    ReconstructionBackendId.COLMAP_OPENMVS,
                    configuration={"preset": BUILD_PRESET, "capture_id": capture_id, **DETERMINISM},
                    requested_capabilities=(
                        ReconstructionCapability.SPARSE,
                        ReconstructionCapability.DENSE,
                        ReconstructionCapability.MESH,
                        ReconstructionCapability.TEXTURE,
                    ),
                ),
                workspace.relative_path,
                provenance,
                stages,
                configuration={"preset": BUILD_PRESET, **DETERMINISM},
            )
            execution = ReconstructionExecutionService(jobs, workspaces).execute(
                job_id, workspace, request, cancel=token
            )
        except Exception as error:  # surfaced to the owner; job and workspace fail closed
            reason = f"{type(error).__name__}: {str(error)[:300]}"
            if workspace is not None and workspace.path.is_dir():
                try:
                    if cancelled():
                        workspaces.cancel(workspace, "cancelled before start")
                    else:
                        workspaces.fail(workspace, reason)
                except Exception:
                    pass  # already terminal
            if cancelled():  # cancel won the race with job start
                try:
                    jobs.finish_cancel(job_id)
                except Exception:
                    pass
                finish("cancelled", "Build cancelled; the imported scan is unchanged.")
                return
            try:
                if jobs.get(job_id).state not in TERMINAL_STATES:
                    jobs.fail(job_id, reason)
            except Exception:
                pass
            finish("failed", f"Build failed: {reason}")
            return

        result = execution.result
        if result.status is RunStatus.CANCELLED:
            finish("cancelled", "Build cancelled; the imported scan is unchanged.")
            return
        if result.status is RunStatus.FAILED or result.output is None:
            finish("failed", f"Build failed: {result.failure_reason or 'unknown reason'}")
            return
        paths = {key: layout.root / value for key, value in result.output.asset_paths.items()}
        model = paths.get("dense-point-cloud:point_cloud") or paths.get(
            "texture-mesh:textured_mesh"
        )
        registered = facts.get("registered_images")
        count = (
            f"{registered}/{facts.get('input_images')} photos registered, "
            if registered is not None
            else ""
        )
        finish(
            "succeeded",
            f"Model built: {count}{time.monotonic() - started:.0f} s.",
            model_path=model,
            textured_mesh_path=paths.get("texture-mesh:textured_mesh"),
        )


# ------------------------------------------------------------------------------- view


class BuildModelView(QWidget):
    """Reconstruction route: progress, cancel and next steps for the latest build."""

    open_model_requested = Signal(object)  # Path
    route_requested = Signal(str)

    def __init__(self, jobs: JobManager | None = None) -> None:
        super().__init__()
        self.setObjectName("packlab.view.reconstruction")
        self.jobs = jobs
        self.job_id: str | None = None
        self.result: BuildResult | None = None
        self.title = QLabel("Build 3D model", self)
        self.status = QLabel(
            "Select a scan in Capture Inbox and press Build model, or import one with "
            "automatic building switched on in Settings.",
            self,
        )
        self.status.setWordWrap(True)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setEnabled(False)
        self.open_button = QPushButton("Open model in viewer", self)
        self.open_button.setEnabled(False)
        self.next_steps = QLabel(NEXT_STEPS, self)
        self.next_steps.setWordWrap(True)
        self.next_steps.setVisible(False)
        steps = QHBoxLayout()
        for text, route in (
            ("Object-only, scale and measure", "measure-design"),
            ("Design Model / Scan Master", "measure-design"),
            ("Labels", "labels"),
            ("Export", "exports"),
        ):
            button = QPushButton(text, self)
            button.clicked.connect(lambda _=False, value=route: self.route_requested.emit(value))
            steps.addWidget(button)
        steps.addStretch(1)
        self.steps_row = QWidget(self)
        self.steps_row.setLayout(steps)
        self.steps_row.setVisible(False)
        buttons = QHBoxLayout()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.open_button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addLayout(buttons)
        layout.addWidget(self.next_steps)
        layout.addWidget(self.steps_row)
        layout.addStretch(1)
        self.cancel_button.clicked.connect(self._cancel)
        self.open_button.clicked.connect(self._open)
        if jobs is not None:
            jobs.job_changed.connect(self._job_changed)

    def track(self, job_id: str, capture_id: str) -> None:
        self.job_id = job_id
        self.result = None
        self.title.setText(f"Building 3D model of {capture_id}")
        self.status.setText("Queued: preparing photos…")
        self.progress.setValue(0)
        self.cancel_button.setEnabled(True)
        self.open_button.setEnabled(False)
        self.next_steps.setVisible(False)
        self.steps_row.setVisible(False)

    def _job_changed(self, job_id: str) -> None:
        if job_id != self.job_id or self.jobs is None:
            return
        job = self.jobs.get(job_id)
        self.progress.setValue(int(job.progress * 100))
        if job.state is JobState.CANCELLING:
            self.status.setText("Cancelling…")
        elif job.message and job.state is JobState.RUNNING:
            self.status.setText(job.message)
        self.cancel_button.setEnabled(job.state in {JobState.QUEUED, JobState.RUNNING})

    def _cancel(self) -> None:
        if self.jobs is not None and self.job_id is not None:
            job = self.jobs.get(self.job_id)
            if job.state not in TERMINAL_STATES:
                self.jobs.request_cancel(self.job_id)

    def show_result(self, result: BuildResult) -> None:
        if result.job_id != self.job_id:
            return
        self.result = result
        self.cancel_button.setEnabled(False)
        self.status.setText(result.message)
        succeeded = result.status == "succeeded" and result.model_path is not None
        if succeeded:
            self.progress.setValue(100)
        self.open_button.setEnabled(succeeded)
        self.next_steps.setVisible(succeeded)
        self.steps_row.setVisible(succeeded)

    def _open(self) -> None:
        if self.result is not None and self.result.model_path is not None:
            self.open_model_requested.emit(self.result.model_path)


__all__ = [
    "BuildBackend",
    "BuildModelController",
    "BuildModelError",
    "BuildModelView",
    "BuildResult",
    "ColmapOpenMvsBackend",
    "MainThreadInvoker",
    "register_raw_capture",
]
