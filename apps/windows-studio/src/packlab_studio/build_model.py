"""Build model: run one imported scan through the COLMAP/OpenMVS lane in the background.

The heavy work runs on a worker thread. Every JobManager call is marshalled back to
the Qt main thread, so job state keeps a single writer. Reconstruction itself goes
through the existing ReconstructionExecutionService -> ReconstructionOrchestrator,
inside a project-scoped ReconstructionWorkspace whose source is the RAW_CAPTURE.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import struct
import threading
import time
import uuid
import zipfile
from collections.abc import Callable, Sequence
from contextlib import closing
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Protocol, cast

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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

from .capture_inbox import effective_role, inbox_row, local_time, parts_summary_text
from .engine_config import DiscoveryStatus, discover_engines
from .i18n import tr
from .jobs import TERMINAL_STATES, JobManager, JobRecord, JobState
from .project import ProjectManager
from .reconstruction_execution import ReconstructionExecutionService
from .reconstruction_workspace import ReconstructionWorkspace, ReconstructionWorkspaceManager

BUILD_PRESET = "studio-cpu-v1"  # High quality: the original pipeline
# Build quality presets (Settings > Build quality). Fast cuts an 81-photo CPU build from ~2 h:
# match only capture-order neighbour pairs instead of every pair, densify at 750 px
# depth maps and texture a decimated ReconstructMesh output without RefineMesh.
BUILD_QUALITIES = {"fast": "studio-cpu-fast-v1", "high": BUILD_PRESET}
DEFAULT_BUILD_QUALITY = "fast"
# Fast pair list: the iOS guide takes about RING_SIZE photos per height ring in capture
# order (owner scan 2026-11-27: rings of 16-17 photos), so the adjacent-ring partner of a
# photo is index +/- RING_SIZE, give or take one.
# ponytail: ring size is a calibration knob for the current guide; read it from the package
# if the guide ever records rings.
FAST_MATCH_OVERLAP = 12
RING_SIZE = 16
# 2000 px photos: level 1 gives 1000 px depth maps; Fast caps them at 750 px. (Level 2
# alone changes nothing: 500 px is under OpenMVS's --min-resolution 640.) Owner scan
# 2026-11-27: 750 px densified in 8 min vs 13 min and kept the 35-40 mm cap; 500 px
# took about as long and widened the measured base slice by 5 mm.
DENSIFY_ARGS = {
    "fast": ("--resolution-level", "1", "--max-resolution", "750"),
    "high": ("--resolution-level", "1"),
}
# Without RefineMesh (which decimates, ~370k faces on the 81-photo scan) the raw ~2M-face
# ReconstructMesh surface made TextureMesh take 35 min; Fast decimates it to this size.
FAST_MESH_FACES = 400_000
MAX_IMAGE_SIZE = 2000  # long side; keeps CPU-only laptops at minutes, not hours
HEIC_SUFFIXES = {".heic", ".heif"}
COPY_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
# The command plan uses COLMAP 4.x option names (FeatureExtraction.*, FeatureMatching.*);
# 4.2.1 is the version it was verified with (Test-333) and the one PL-0444 bundles.
SUPPORTED_COLMAP_VERSIONS = ("4.2.1",)
# PL-0463 reproducibility: fixed COLMAP seeds (RANSAC + mapper sampling), a single-threaded
# mapper (threaded bundle adjustment sums in a varying order) and sorted image order.
# Three Test-333 builds then gave bit-identical sparse models. Feature extraction runs on
# many threads: SIFT per image is deterministic, only COLMAP 4.2.1's image numbering follows
# completion order, so canonicalize_image_ids() renumbers by sorted name afterwards. On an
# 81-photo owner scan: 16 threads 199 s vs 1 thread ~17-20 min, and every database table
# is then identical to the 1-thread run. Not fixed, documented: CPU
# matching uses an approximate (FAISS) index that is not guaranteed repeatable (one standalone
# repeat differed; the exact brute-force matcher took 704 s instead of 38 s), and OpenMVS
# 2.4.0 has no seed option (densify of one identical scene gave 167,891 vs 168,892 points).
RANDOM_SEED = 0  # --default_random_seed 0 is COLMAP's default; passed so the plan records it
MAPPER_THREADS = 1
DEFAULT_MAX_CONCURRENT_BUILDS = 2  # scans are separate objects; never merged into one model
# Below this share of connected photos the model is too partial to measure; stop before
# the long dense stages and tell the owner to retake (real scan 2026-11-22: 3/17).
MIN_REGISTERED_FRACTION = 0.5
# TextureMesh tries in order; any abnormal exit moves on, the last resort is no texture.
TEXTURE_ATTEMPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("scene_textured", ()),
    ("scene_textured_noseam", ("--global-seam-leveling", "0", "--local-seam-leveling", "0")),
)
TEXTURE_OUTCOMES = {  # facts["texture"]; 0 = every attempt failed
    1: "textured",
    2: "textured with seam leveling off (default texturing crashed)",
    0: "texture unavailable (texturing crashed twice; untextured mesh)",
}
TEXTURE_NOTES = {
    TEXTURE_OUTCOMES[2]: "Texture made with seam leveling off after the texturing engine crashed.",
    TEXTURE_OUTCOMES[0]: (
        "Texture unavailable: the texturing engine crashed, so the model has no colour "
        "texture. The shape is not affected."
    ),
}


def worker_threads(builds_running: int) -> int:
    """CPU threads for one stage while builds_running builds (itself included) run."""
    # Decided at every stage start, so running builds together use at most the cores; the only
    # overshoot is a build that started a stage before another build began, until its next
    # stage. A lone build keeps all cores: matching 30 photos took 141 s on 16 threads vs
    # 231 s on 8 (16 logical cores).
    return max(1, (os.cpu_count() or 1) // max(1, builds_running))


def determinism(
    max_concurrent_builds: int = 1, quality: str = DEFAULT_BUILD_QUALITY
) -> dict[str, object]:
    """The recorded seeds, thread policy and concurrency of one build (DETERMINISM block)."""
    fast = quality == "fast"
    return {
        "build_quality": quality,
        "matching": (
            f"pair list: capture-order overlap {FAST_MATCH_OVERLAP} + quadratic, "
            f"ring closure and adjacent rings (ring size {RING_SIZE})"
            if fast
            else "exhaustive"
        ),
        "densify": " ".join(DENSIFY_ARGS[quality]),
        "mesh_refinement": (
            f"skipped; reconstructed mesh decimated to {FAST_MESH_FACES} faces"
            if fast
            else "RefineMesh"
        ),
        "colmap_random_seed": RANDOM_SEED,
        "colmap_mapper_threads": MAPPER_THREADS,
        "cpu_count": os.cpu_count() or 1,
        # extraction, matching, densify and refine; each stage's stdout ends with its count
        "worker_threads": "cpu_count // builds running at stage start",
        "max_concurrent_builds": max_concurrent_builds,
        "image_order": "capture_sequence",  # working names start with the capture position
        "image_ids": "canonical_sorted_name",
        "texture_fallback": "default, then seam leveling off, then untextured mesh",
    }


DETERMINISM = determinism()


def canonicalize_image_ids(database: Path) -> None:
    """Renumber a fresh COLMAP 4.2.1 database so image (and frame) ids follow sorted names.

    Multi-threaded feature extraction writes images in completion order; keypoints and
    descriptors per image are identical, so renumbering gives the single-thread database.
    """
    with closing(sqlite3.connect(database)) as db, db:

        def count(table: str) -> int:
            return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

        rows = db.execute("SELECT image_id, name FROM images").fetchall()
        ids = {image_id for image_id, _ in rows}
        frames = db.execute("SELECT frame_id, data_id, sensor_type FROM frame_data").fetchall()
        if count("matches") or count("two_view_geometries"):
            raise BuildModelError("COLMAP database already has matches; renumbering refused")
        if count("rig_sensors") or count("frames") != len(rows):
            raise BuildModelError("COLMAP database has a multi-camera rig; renumbering refused")
        if sorted(frames) != sorted((image_id, image_id, 0) for image_id in ids):
            raise BuildModelError("COLMAP frames do not map one-to-one to images")
        priors = db.execute("SELECT corr_data_id, corr_sensor_type FROM pose_priors").fetchall()
        if any(data_id not in ids or sensor_type != 0 for data_id, sensor_type in priors):
            raise BuildModelError("COLMAP pose priors (photo GPS) do not refer to the images")
        offset = 1_000_000_000
        columns = (
            ("images", "image_id"),
            ("keypoints", "image_id"),
            ("descriptors", "image_id"),
            ("frames", "frame_id"),
            ("frame_data", "frame_id"),
            ("frame_data", "data_id"),
            ("pose_priors", "corr_data_id"),  # GPS priors from photo EXIF follow their image
        )
        for table, column in columns:
            db.execute(f"UPDATE {table} SET {column} = {column} + ?", (offset,))
        for new, (old, _name) in enumerate(sorted(rows, key=lambda row: row[1]), start=1):
            for table, column in columns:
                db.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (new, old + offset)
                )


def fast_match_pairs(count: int) -> list[tuple[int, int]]:
    """Image index pairs (capture order) for the Fast preset, i < j, sorted.

    Neighbours within FAST_MATCH_OVERLAP, quadratic jumps beyond it (like COLMAP's
    sequential matcher), the wrap-around of each height ring, and the same azimuth wedge
    in the adjacent ring (index +/- RING_SIZE). No vocabulary tree is bundled, so there is
    no loop detection.
    """
    pairs: set[tuple[int, int]] = set()
    for i in range(count):
        pairs.update((i, j) for j in range(i + 1, min(count, i + FAST_MATCH_OVERLAP + 1)))
        step = 1
        while i + step < count:
            if step > FAST_MATCH_OVERLAP:
                pairs.add((i, i + step))
            step *= 2
        pairs.update((i, j) for j in range(i + RING_SIZE - 1, i + RING_SIZE + 2) if j < count)
        start = i - i % RING_SIZE
        for k in (1, 2):  # ring closure: the last photos of a ring meet its first ones
            j = start + (i - start + RING_SIZE - k) % RING_SIZE
            if i < j < count:
                pairs.add((i, j))
    return sorted(pairs)


def capture_sequence(package: Path) -> dict[str, int]:
    """{"images/<file>": sequence} from the package's metadata/photos.json; {} if absent.

    Only orders photos; a package without sequences falls back to name order.
    """
    try:
        with zipfile.ZipFile(package) as archive:
            photos = json.loads(archive.read("metadata/photos.json")).get("photos")
        return {
            photo["image_path"]: photo["sequence"]
            for photo in photos
            if isinstance(photo.get("image_path"), str) and type(photo.get("sequence")) is int
        }
    except (OSError, KeyError, ValueError, TypeError, AttributeError, zipfile.BadZipFile):
        return {}


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
    max_concurrent_builds: int = 1
    quality: str = DEFAULT_BUILD_QUALITY
    builds_running: Callable[[], int] = lambda: 1  # read at every stage start

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
        fast = self.quality == "fast"
        mesh_ply = mvs / ("scene_dense_mesh.ply" if fast else "scene_refined.ply")
        colmap = str(self.colmap)
        tool = {key: str(value) for key, value in self.openmvs.items()}
        used: dict[str, int] = {}

        def threads(stage_id: str) -> str:
            used[stage_id] = worker_threads(self.builds_running())
            return str(used[stage_id])

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
            if stage_id in used:  # recorded with the stage result in the run manifest
                note = f"\n[packlab] {stage_id} ran with {used[stage_id]} threads\n"
                result = replace(result, stdout=result.stdout + note)
            return ReconstructionStageExecution(
                stage_id,
                result,
                {name: asset(path) for name, path in outputs.items()},
                outputs_verified=result.status is StageStatus.SUCCEEDED,
            )

        def features(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            images.mkdir(parents=True, exist_ok=True)
            commands: list[tuple[Sequence[str], Path]] = []
            # Capture order (photos.json sequence), then name. The working name starts with
            # the position, so COLMAP's sorted-name image ids follow the capture too.
            sequence = cast(dict[str, int], facts.get("capture_sequence") or {})
            inputs = f"{workspace_asset}/inputs"

            def order(item: str) -> tuple[int, str]:
                key = Path(item).relative_to(inputs).as_posix()
                return (sequence.get(key, 1 << 62), working_image_name(Path(item)))

            sources = [
                w / Path(item).relative_to(workspace_asset)
                for item in sorted(context.job.inputs.image_asset_ids, key=order)
            ]
            for position, source in enumerate(sources):
                suffix = source.suffix.lower()
                name = f"{position:04d}_{working_image_name(source)}"
                if suffix in HEIC_SUFFIXES:
                    if self.ffmpeg is None:
                        raise BuildModelError("HEIC photos need ffmpeg; set PACKLAB_FFMPEG_PATH")
                    commands.append((heic_decode_command(self.ffmpeg, source, images / name), w))
                elif suffix in COPY_SUFFIXES:
                    shutil.copyfile(source, images / name)
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
                        threads("feature-extraction"),
                    ),
                    w,
                )
            )
            # ponytail: photos decode one at a time; parallelize if decode dominates.
            result = _run_commands("feature-extraction", commands, context.cancel)
            if result.status is StageStatus.SUCCEEDED:
                canonicalize_image_ids(database)
            return done("feature-extraction", result, {"database": database, "images": images})

        def matching(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            matcher: tuple[str, ...] = ("exhaustive_matcher",)
            if fast:
                names = sorted(path.name for path in images.glob("*"))  # capture order
                pair_list = out / "colmap/match_pairs.txt"
                pair_list.parent.mkdir(parents=True, exist_ok=True)
                pair_list.write_text(
                    "".join(f"{names[i]} {names[j]}\n" for i, j in fast_match_pairs(len(names))),
                    encoding="utf-8",
                )
                matcher = ("matches_importer", "--match_list_path", str(pair_list))
                matcher += ("--match_type", "pairs")
            result = _run_commands(
                "matching",
                [
                    (
                        (
                            colmap,
                            *matcher,
                            "--database_path",
                            str(database),
                            "--FeatureMatching.use_gpu",
                            "0",
                            "--FeatureMatching.num_threads",
                            threads("matching"),
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
            facts["registered_images"] = registered = _registered_images(best)
            total = cast(int, facts.get("input_images") or 0)
            if total and registered < MIN_REGISTERED_FRACTION * total:
                raise BuildModelError(
                    f"only {registered} of {total} photos could be connected - the photos are "
                    "too far apart or do not overlap. Retake the scan following the phone's "
                    "order (one photo every step, all heights) and keep the package in view."
                )
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
                            *DENSIFY_ARGS[self.quality],
                            "--max-threads",
                            threads("dense-point-cloud"),
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
                [
                    (
                        (
                            tool["reconstruct_mesh"],
                            "scene_dense.mvs",
                            "-p",
                            "scene_dense.ply",
                            *(("--target-face-num", str(FAST_MESH_FACES)) if fast else ()),
                        ),
                        mvs,
                    )
                ],
                context.cancel,
            )
            return done("mesh-reconstruction", result, {"mesh": mvs / "scene_dense_mesh.ply"})

        def refine(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            if fast:  # RefineMesh took ~22 of ~120 min on an 81-photo CPU build
                note = "[packlab] mesh-refinement skipped (Fast preset); texturing the mesh\n"
                skipped = ReconstructionStageResult(
                    "mesh-refinement", StageStatus.SUCCEEDED, 0, 0.0, note, ""
                )
                return done("mesh-refinement", skipped, {"mesh": mesh_ply})
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
                            threads("mesh-refinement"),
                        ),
                        mvs,
                    )
                ],
                context.cancel,
            )
            return done("mesh-refinement", result, {"mesh": mvs / "scene_refined.ply"})

        def texture(context: ReconstructionStageContext) -> ReconstructionStageExecution:
            # OpenMVS 2.4.0 TextureMesh can crash (0xC0000005) in seam leveling on real scans
            # (owner build 2026-11-27, 81 photos); the same scene textures with leveling off.
            def attempt(name: str, *extra: str) -> ReconstructionStageResult:
                args = (tool["texture_mesh"], "scene_dense.mvs", "-m", mesh_ply.name)
                return _run_commands(
                    "texture-mesh",
                    [((*args, "-o", f"{name}.mvs", "--export-type", "obj", *extra), mvs)],
                    context.cancel,
                )

            def produced(result: ReconstructionStageResult, name: str) -> bool:
                obj = mvs / f"{name}.obj"
                return (
                    result.status is StageStatus.SUCCEEDED
                    and obj.is_file()
                    and obj.stat().st_size > 0
                )

            notes: list[str] = []
            seconds = 0.0
            for number, (name, extra) in enumerate(TEXTURE_ATTEMPTS, start=1):
                result = attempt(name, *extra)
                seconds += result.duration_seconds
                if result.status is StageStatus.CANCELLED:
                    return done("texture-mesh", result, {})
                if produced(result, name):
                    facts["texture"] = TEXTURE_OUTCOMES[number]
                    note = f"[packlab] texture-mesh: attempt {number} ({name}) produced the model"
                    result = replace(
                        result,
                        duration_seconds=seconds,
                        stdout="\n".join([result.stdout, *notes, note]),
                    )
                    return done("texture-mesh", result, {"textured_mesh": mvs / f"{name}.obj"})
                notes.append(
                    f"[packlab] texture-mesh: attempt {number} ({name}) failed: "
                    f"{result.failure_reason or 'no textured mesh written'}"
                )
            facts["texture"] = TEXTURE_OUTCOMES[0]
            note = "[packlab] texture-mesh: texture unavailable; the model is the untextured mesh"
            result = ReconstructionStageResult(
                "texture-mesh",
                StageStatus.SUCCEEDED,
                0,
                seconds,
                "\n".join([result.stdout[-8_000:], *notes, note]),
                result.stderr[-8_000:],
            )
            return done("texture-mesh", result, {"mesh": mesh_ply})

        executors = (features, matching, mapping, conversion, densify, mesh, refine, texture)
        return _definitions(
            executors,
            {
                "preset": BUILD_QUALITIES[self.quality],
                "max_image_size": MAX_IMAGE_SIZE,
                **determinism(self.max_concurrent_builds, self.quality),
            },
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
    """Queues one background build per request (up to max_concurrent at once, FIFO)."""

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
        self.max_concurrent = DEFAULT_MAX_CONCURRENT_BUILDS
        self.quality = DEFAULT_BUILD_QUALITY
        self._queue: list[tuple[str, str, Callable[[], None]]] = []  # FIFO, not yet started
        self._running: set[str] = set()
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

        recorded = determinism(self.max_concurrent, self.quality)
        worker = backend
        if isinstance(worker, ColmapOpenMvsBackend):
            worker = replace(
                worker,
                max_concurrent_builds=self.max_concurrent,
                quality=self.quality,
                builds_running=lambda: len(self._running),
            )

        def start() -> None:
            threading.Thread(
                target=self._work,
                args=(
                    job.job_id,
                    capture_id,
                    worker,
                    layout,
                    metadata,
                    source_asset,
                    package_sha256,
                    token,
                    recorded,
                ),
                name=f"packlab-build-{job.job_id[:8]}",
                daemon=True,
            ).start()

        self._by_package[package_sha256] = job.job_id
        self._queue.append((job.job_id, capture_id, start))
        self.build_started.emit(job.job_id, capture_id)
        self._start_next()
        return job.job_id

    def set_quality(self, quality: object) -> None:
        """Applies to builds started afterwards; unknown values fall back to Fast."""
        self.quality = str(quality) if str(quality) in BUILD_QUALITIES else DEFAULT_BUILD_QUALITY

    def set_max_concurrent(self, limit: int) -> None:
        self.max_concurrent = max(1, limit)
        self._start_next()

    def _start_next(self) -> None:
        dropped: list[BuildResult] = []
        while len(self._running) < self.max_concurrent and self._queue:
            job_id, capture_id, start = self._queue.pop(0)
            if self.jobs.get(job_id).state in TERMINAL_STATES:  # cancelled while queued
                dropped.append(BuildResult(job_id, capture_id, "cancelled", "Build cancelled."))
                continue
            self._running.add(job_id)
            start()
        for result in dropped:
            self.build_finished.emit(result)

    def _on_finished(self, result: BuildResult) -> None:
        self._running.discard(result.job_id)
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
        recorded: dict[str, object],
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
            facts["capture_sequence"] = capture_sequence(layout.root / source_asset)
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
            preset = BUILD_QUALITIES[str(recorded["build_quality"])]
            request = ReconstructionOrchestrationRequest(
                ReconstructionJobSpec(
                    job_id,
                    metadata.project_id,
                    metadata.revision,
                    working_set.inputs,
                    ReconstructionBackendId.COLMAP_OPENMVS,
                    configuration={"preset": preset, "capture_id": capture_id, **recorded},
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
                configuration={"preset": preset, **recorded},
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
        note = TEXTURE_NOTES.get(str(facts.get("texture")))
        finish(
            "succeeded",
            f"Model built: {count}{time.monotonic() - started:.0f} s."
            + ("" if note is None else " " + tr(note)),
            model_path=model,
            textured_mesh_path=paths.get("texture-mesh:textured_mesh"),
        )


# ------------------------------------------------------------------------------- view


class BuildModelView(QWidget):
    """Reconstruction route: progress, cancel and next steps for the latest build."""

    open_model_requested = Signal(object)  # Path
    route_requested = Signal(str)
    build_requested = Signal(str, str)  # capture_id, package_sha256 (F16 scan list)

    def __init__(self, jobs: JobManager | None = None) -> None:
        super().__init__()
        self.setObjectName("packlab.view.reconstruction")
        self.jobs = jobs
        self.job_id: str | None = None
        self.result: BuildResult | None = None
        # PL-0490: every build started from this page (FIFO = queue order) and its last step.
        self._tracked: dict[str, str] = {}  # job_id -> capture_id
        self._steps: dict[str, str] = {}  # job_id -> last progress message ("5/8 ...")
        self._history_args: tuple[list[Any], Path | None, dict[str, str] | None] | None = None
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
        # F16: the project's scans and their latest build, not only the running one.
        self.history = QListWidget(self)
        self.history.setObjectName("packlab.reconstruction.history")
        self.history.setMinimumHeight(140)
        self.build_selected_button = QPushButton(tr("Build selected scan"), self)
        self.build_selected_button.setObjectName("packlab.reconstruction.build-selected")
        self.open_selected_button = QPushButton(tr("Open selected model"), self)
        self.open_selected_button.setObjectName("packlab.reconstruction.open-selected")
        history_buttons = QHBoxLayout()
        history_buttons.addWidget(self.build_selected_button)
        history_buttons.addWidget(self.open_selected_button)
        history_buttons.addStretch(1)
        history_box = QGroupBox(tr("Scans and builds"), self)
        history_layout = QVBoxLayout(history_box)
        history_layout.addWidget(self.history, 1)
        # PL-0482: which part scans (closure/body/assembled, upright/upside down) exist.
        self.parts_label = QLabel("", self)
        self.parts_label.setObjectName("packlab.reconstruction.parts")
        self.parts_label.setTextFormat(Qt.TextFormat.PlainText)
        history_layout.addWidget(self.parts_label)
        history_layout.addLayout(history_buttons)
        layout.addWidget(history_box, 1)
        self.history.currentRowChanged.connect(lambda _row: self._history_selected())
        self.build_selected_button.clicked.connect(self._build_selected)
        self.open_selected_button.clicked.connect(self._open_selected)
        self._history_selected()
        self.cancel_button.clicked.connect(self._cancel)
        self.open_button.clicked.connect(self._open)
        if jobs is not None:
            jobs.job_changed.connect(self._job_changed)

    def track(self, job_id: str, capture_id: str) -> None:
        self._tracked[job_id] = capture_id
        self.result = None
        self.open_button.setEnabled(False)
        self.next_steps.setVisible(False)
        self.steps_row.setVisible(False)
        if self._job(job_id) is None:
            self.job_id = job_id
            self.title.setText(tr("Building 3D model of {captures}").format(captures=capture_id))
            self.status.setText(tr("Queued: preparing photos…"))
            self.progress.setValue(0)
            self.cancel_button.setEnabled(True)
            return
        self._update_header()

    def _job(self, job_id: str | None) -> JobRecord | None:
        """The job record, or None (no job manager, unknown id or trimmed from history)."""
        try:
            return None if self.jobs is None or job_id is None else self.jobs.get(job_id)
        except KeyError:
            return None

    def _active_jobs(self) -> tuple[list[str], list[str]]:
        """Running (incl. cancelling) and queued tracked builds, oldest first."""
        running: list[str] = []
        queued: list[str] = []
        for job_id in self._tracked:
            job = self._job(job_id)
            state = None if job is None else job.state
            if state in {JobState.RUNNING, JobState.CANCELLING}:
                running.append(job_id)
            elif state is JobState.QUEUED:
                queued.append(job_id)
        return running, queued

    def _live_text(self, job_id: str) -> str:
        """'building 50% - step 5/8 ...', 'queued #2', 'cancelling', or a terminal state."""
        assert self.jobs is not None
        job = self.jobs.get(job_id)
        if job.state is JobState.QUEUED:
            _running, queued = self._active_jobs()
            return tr("queued #{position}").format(position=queued.index(job_id) + 1)
        if job.state is JobState.CANCELLING:
            return tr("cancelling")
        if job.state is JobState.RUNNING:
            step = self._steps.get(job_id)
            percent = int(job.progress * 100)
            if step:
                return tr("building {percent}% - step {step}").format(percent=percent, step=step)
            return tr("building {percent}%").format(percent=percent)
        if job.state is JobState.FAILED:
            return tr("failed: {reason}").format(
                reason=plain_failure(job.error or "", self._steps.get(job_id))
            )
        return tr("cancelled") if job.state is JobState.CANCELLED else tr("built")

    def _update_header(self) -> None:
        """PL-0490: the header shows every running build and the queue, oldest first."""
        running, queued = self._active_jobs()
        if not running and not queued:
            return  # show_result owns the finished state
        self.job_id = (running or queued)[0]
        names = [self._tracked[job_id][:8] for job_id in running or queued]
        title = "Building 3D model of {captures}" if running else "Waiting to build {captures}"
        self.title.setText(tr(title).format(captures=", ".join(names)))
        lines = [
            tr("{capture}: {state}").format(
                capture=self._tracked[job_id][:8], state=self._live_text(job_id)
            )
            for job_id in running
        ]
        if queued:
            waiting = ", ".join(
                f"#{index} {self._tracked[job_id][:8]}" for index, job_id in enumerate(queued, 1)
            )
            lines.append(tr("Queued: {captures}").format(captures=waiting))
        if self.result is not None:
            lines.append(tr("Last finished: {message}").format(message=self._result_text()))
        self.status.setText("\n".join(lines))
        assert self.jobs is not None
        self.progress.setValue(int(self.jobs.get(self.job_id).progress * 100))
        self.cancel_button.setEnabled(True)

    def _job_changed(self, job_id: str) -> None:
        if job_id not in self._tracked or self.jobs is None:
            return
        job = self.jobs.get(job_id)
        if job.state is JobState.RUNNING and job.message:
            self._steps[job_id] = job.message
        self._update_header()
        if self._history_args is not None:
            self.refresh_history(*self._history_args)

    def _cancel(self) -> None:
        if self.jobs is not None and self.job_id is not None:
            job = self.jobs.get(self.job_id)
            if job.state not in TERMINAL_STATES:
                self.jobs.request_cancel(self.job_id)

    def _result_text(self) -> str:
        result = self.result
        assert result is not None
        if result.status != "failed":
            return result.message
        reason = result.message.removeprefix("Build failed: ")
        return tr("Build failed: {reason}").format(
            reason=plain_failure(reason, self._steps.get(result.job_id))
        )

    def show_result(self, result: BuildResult) -> None:
        if result.job_id != self.job_id and result.job_id not in self._tracked:
            return
        self.result = result
        succeeded = result.status == "succeeded" and result.model_path is not None
        self.open_button.setEnabled(succeeded)
        self.next_steps.setVisible(succeeded)
        self.steps_row.setVisible(succeeded)
        running, queued = self._active_jobs()
        if running or queued:
            self._update_header()
            return
        self.job_id = result.job_id
        self.cancel_button.setEnabled(False)
        self.status.setText(self._result_text())
        self.status.setToolTip(result.message)  # the technical reason stays available
        if succeeded:
            self.progress.setValue(100)

    def _open(self) -> None:
        if self.result is not None and self.result.model_path is not None:
            self.open_model_requested.emit(self.result.model_path)

    def refresh_history(
        self,
        entries: list[Any],
        project_root: Path | None,
        roles: dict[str, str] | None = None,
    ) -> None:
        """One row per imported scan with its live build state, else its latest build here."""
        self._history_args = (entries, project_root, roles)
        row = self.history.currentRow()
        builds = latest_builds(project_root)
        self.history.clear()
        self.parts_label.setText(
            parts_summary_text(entries, roles, project_scan_digests(project_root))
        )
        live = {capture: job_id for job_id, capture in self._tracked.items()}  # latest job wins
        for entry in entries:
            if entry.status != "imported":
                continue
            text, details = inbox_row(entry, effective_role(entry, roles))
            build = builds.get(entry.package_sha256)
            state = self._scan_state(live.get(entry.capture_id), build)
            item = QListWidgetItem(f"{text}   ·   {state}")
            item.setToolTip(details)
            item.setData(Qt.ItemDataRole.UserRole, (entry.capture_id, entry.package_sha256))
            item.setData(Qt.ItemDataRole.UserRole + 1, None if build is None else build["model"])
            self.history.addItem(item)
        if not self.history.count():
            self.history.addItem(tr("No imported scans yet: use Capture Inbox first."))
        if 0 <= row < self.history.count():
            self.history.setCurrentRow(row)
        self._history_selected()

    def _scan_state(self, job_id: str | None, build: dict[str, Any] | None) -> str:
        """Live job state first; a workspace no job owns (e.g. after restart) is interrupted."""
        job = self._job(job_id)
        if job is not None and (job.state not in TERMINAL_STATES or job.state is JobState.FAILED):
            return self._live_text(str(job_id))
        if build is None:
            return tr("cancelled") if job is not None else tr("not built yet")
        state = str(build["state"])
        if state == "succeeded":
            return tr("built {time}").format(time=local_time(build["time"]))
        if state == "failed":
            return tr("failed: {reason}").format(reason=plain_failure(str(build["reason"] or "")))
        if state == "active":
            return tr("interrupted")
        return tr("cancelled") if state == "cancelled" else state

    def _history_selected(self) -> None:
        item = self.history.currentItem()
        scan = None if item is None else item.data(Qt.ItemDataRole.UserRole)
        model = None if item is None else item.data(Qt.ItemDataRole.UserRole + 1)
        self.build_selected_button.setEnabled(bool(scan))
        self.open_selected_button.setEnabled(model is not None)

    def _build_selected(self) -> None:
        item = self.history.currentItem()
        scan = None if item is None else item.data(Qt.ItemDataRole.UserRole)
        if scan:
            self.build_requested.emit(str(scan[0]), str(scan[1]))

    def _open_selected(self) -> None:
        item = self.history.currentItem()
        model = None if item is None else item.data(Qt.ItemDataRole.UserRole + 1)
        if model is not None:
            self.open_model_requested.emit(Path(model))


_STEP_NAMES = {
    "feature-extraction": ("photo decoding step", "COLMAP"),
    "matching": ("photo matching step", "COLMAP"),
    "sparse-mapping": ("camera solving step", "COLMAP"),
    "openmvs-conversion": ("dense scene preparation step", "OpenMVS"),
    "dense-point-cloud": ("dense point cloud step", "OpenMVS"),
    "mesh-reconstruction": ("mesh step", "OpenMVS"),
    "mesh-refinement": ("mesh refinement step", "OpenMVS"),
    "texture-mesh": ("texture step", "OpenMVS"),
}
# Windows NTSTATUS crash exit codes, unsigned and signed: access violation, stack overflow,
# heap corruption, illegal instruction.
_CRASH_CODES = frozenset(
    (3221225477, -1073741819, 3221225725, -1073741571, 3221226356, -1073740940)
    + (3221225501, -1073741795)
)


def plain_failure(reason: str, step: str | None = None) -> str:
    """Plain words for a build failure: 'stage exited 3221225477' -> 'texture step crashed'.

    ``step`` is the job's last progress message ("8/8 Texturing the mesh"); without it the
    step is unknown. Unrecognised reasons are returned shortened, never invented.
    """
    label = (step or "").partition(" ")[2]
    stage = next((key for key, value in STAGE_LABELS.items() if value == label), "")
    name, engine = _STEP_NAMES.get(stage, ("a build step", ""))
    where = tr(name) + (f" ({engine})" if engine else "")
    exited = re.search(r"\bstage exited (-?\d+)", reason)
    if exited and int(exited.group(1)) in _CRASH_CODES:
        return tr("{step} crashed").format(step=where)
    if exited:
        return tr("{step} stopped with error code {code}").format(step=where, code=exited.group(1))
    if "timed out" in reason.lower() or "timeout" in reason.lower():
        return tr("{step} took too long and was stopped").format(step=where)
    text = re.sub(r"^[A-Za-z]+(Error|Exception): ", "", reason.strip())
    return (text[:117] + "…" if len(text) > 120 else text) or tr("unknown reason")


_MODEL_CANDIDATES = ("outputs/mvs/scene_dense.ply", "outputs/mvs/scene_dense_mesh.ply")


def latest_builds(project_root: Path | None) -> dict[str, dict[str, Any]]:
    """Latest reconstruction workspace per source package digest (read-only scan)."""
    latest: dict[str, dict[str, Any]] = {}
    root = None if project_root is None else project_root / "working" / "reconstruction"
    if root is None or not root.is_dir():
        return latest
    for manifest_path in root.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            when = manifest_path.stat().st_mtime
        except (OSError, ValueError):
            continue
        digest = manifest.get("source_digest") if isinstance(manifest, dict) else None
        if not isinstance(digest, str) or (digest in latest and latest[digest]["time"] > when):
            continue
        model = next(
            (
                manifest_path.parent / name
                for name in _MODEL_CANDIDATES
                if (manifest_path.parent / name).is_file()
            ),
            None,
        )
        latest[digest] = {
            "state": manifest.get("state"),
            "time": when,
            "model": model,
            "reason": manifest.get("reason"),
        }
    return latest


def project_scan_digests(project_root: Path | None) -> set[str]:
    """Package digests imported into this project: a raw copy (queued/built) or a build."""
    digests = set(latest_builds(project_root))
    raw = None if project_root is None else project_root / "raw" / "captures"
    if raw is not None and raw.is_dir():
        digests.update(
            path.stem for path in raw.glob("*.packscan") if re.fullmatch(r"[0-9a-f]{64}", path.stem)
        )
    return digests


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
