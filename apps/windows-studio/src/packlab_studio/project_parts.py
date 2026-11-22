"""Project parts (PL-0485): Closure, Body and Assembled in the Scene / Objects dock.

Each part is built from its upright and upside-down scans (PL-0482 roles). "Combine part"
runs ``align_part_pair`` (PL-0483) on the two dense clouds in a background job and stores
the merged cloud (``derived/parts``), transforms, metrics or the refusal reason in the
project. Merged clouds are in the reference scan's mat frame, mm, METRIC_UNVERIFIED.

"Place closure on body" (PL-0484, on Assembled) registers Body and Closure into the Assembled
cloud (``packlab_core.part_placement``) in a background job and stores the placed clouds
(``derived/parts/*-placed-*.ply``), the scan-level assembly graph revision and clearance
diagnostics, or the typed refusal, in the project.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .build_model import MainThreadInvoker, _MainThreadJobs, latest_builds
from .capture_inbox import counted_role
from .i18n import tr
from .jobs import TERMINAL_STATES, JobManager, JobState
from .project import PROJECT_PARTS, ProjectManager

PART_LABELS = {"closure": "Closure", "body": "Body", "assembled": "Assembled"}
STATUS_TEXT = {
    "missing": "missing",
    "single": "single scan",
    "ready": "both scans, not combined",
    "combined": "combined",
    "refused": "refused",
    "combining": "combining…",
    "placed": "placed",
}
_ROLE = Qt.ItemDataRole.UserRole
PLACEMENT = "placement"  # job key of the closure-on-body placement


@dataclass(frozen=True)
class PartScan:
    package_sha256: str
    model: Path
    time: float


@dataclass(frozen=True)
class PartState:
    part: str
    upright: PartScan | None
    flipped: PartScan | None
    status: str  # see STATUS_TEXT
    reason: str
    cloud: Path | None  # what the viewer shows for this part
    record: dict[str, Any] | None


def part_scans(
    entries: list[Any], overrides: dict[str, str], project_root: Path | None
) -> dict[str, dict[str, PartScan]]:
    """Newest successful build per part view (upright / flipped) in this project."""
    builds = latest_builds(project_root)
    found: dict[str, dict[str, PartScan]] = {part: {} for part in PROJECT_PARTS}
    for entry in entries:
        role = counted_role(entry, overrides, set(builds))
        build = builds.get(entry.package_sha256)
        if role is None or build is None or build["state"] != "succeeded" or not build["model"]:
            continue
        part, _, view = role.partition("_")
        if part not in found or view not in ("", "flipped"):
            continue  # interior scans are PL-0489
        view = view or "upright"
        scan = PartScan(entry.package_sha256, Path(build["model"]), float(build["time"]))
        if view not in found[part] or found[part][view].time < scan.time:
            found[part][view] = scan
    return found


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


_SHA_CACHE: dict[tuple[str, int, int], str] = {}


def _cached_sha(path: Path) -> str | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key not in _SHA_CACHE:
        _SHA_CACHE[key] = _sha256(path)
    return _SHA_CACHE[key]


def _stat(path: Path) -> list[int]:
    stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns]


def _unchanged(path: Path, record: dict[str, Any]) -> bool:
    """Size + mtime as written by the combine job (cheap on the UI thread).

    Records without them (none in the wild yet) fall back to the full digest; Measure &
    Design re-hashes on load (``load_model``) and compares the record's digests.
    """
    try:
        if "file_stat" in record:
            return _stat(path) == record["file_stat"]
    except OSError:
        return False
    return _cached_sha(path) == record.get("file_sha256")


def part_states(
    manager: ProjectManager, entries: list[Any], overrides: dict[str, str]
) -> dict[str, PartState]:
    layout = manager.layout
    root = None if layout is None else layout.root
    scans = part_scans(entries, overrides, root)
    merges = manager.part_merges() if root is not None else {}
    states: dict[str, PartState] = {}
    for part in PROJECT_PARTS:
        up, fl = scans[part].get("upright"), scans[part].get("flipped")
        if up is None and fl is None:
            states[part] = PartState(part, None, None, "missing", "", None, None)
            continue
        if up is None or fl is None:
            single = up or fl
            reason = tr("bottom missing: no upside-down scan") if fl is None else ""
            reason = reason or tr("top missing: no upright scan")
            states[part] = PartState(part, up, fl, "single", reason, single.model, None)  # type: ignore[union-attr]
            continue
        assert root is not None and layout is not None
        record = merges.get(part)
        current = [(s.package_sha256, _rel(root, s.model)) for s in (up, fl)]
        sources = [] if record is None else record.get("sources", [])
        stored = [(s.get("package_sha256"), s.get("model_path")) for s in sources]
        if record is None or stored != current:
            states[part] = PartState(part, up, fl, "ready", "", up.model, None)
        elif record.get("status") == "refused":
            states[part] = PartState(
                part, up, fl, "refused", str(record.get("reason")), up.model, record
            )
        else:
            try:
                cloud = layout.path(
                    "derived", str(record["artifact_path"]).removeprefix("derived/")
                )
            except Exception:
                cloud = None
            if cloud is None or not _unchanged(cloud, record):
                reason = tr("merged cloud missing or changed on disk; combine again")
                states[part] = PartState(part, up, fl, "ready", reason, up.model, None)
            else:
                states[part] = PartState(part, up, fl, "combined", "", cloud, record)
    return states


def _scale_key(state: PartState) -> list[Any] | None:
    """Scales a combined part was built with (None for a single scan)."""
    if state.status != "combined" or state.record is None:
        return None
    return [source.get("mm_per_unit") for source in state.record.get("sources", [])]


def placement_state(
    manager: ProjectManager, states: dict[str, PartState]
) -> tuple[str, dict[str, Any] | None, tuple[Path, ...]]:
    """(none / placed / refused / stale, record, placed body + closure clouds).

    Stale when a part now shows a different cloud (path, content digest, combined/single status
    or combine scale) than the placement used, or a placed cloud is missing or changed on disk.
    A single scan's marker scale is a function of its build, so its cloud digest covers it.
    """
    layout, record = manager.layout, manager.part_placement()
    if layout is None or record is None:
        return "none", None, ()
    sources = record.get("sources")
    for part in ("assembled", "body", "closure"):
        state = states.get(part)
        if state is None or state.cloud is None or not isinstance(sources, dict):
            return "stale", record, ()
        stored = sources.get(part) or {}
        if (
            stored.get("cloud_path") != _rel(layout.root, state.cloud)
            or stored.get("status") != state.status
            or stored.get("scale_key") != _scale_key(state)
            or stored.get("cloud_sha256") != _cached_sha(state.cloud)
        ):
            return "stale", record, ()
    if record.get("status") != "placed":
        return "refused", record, ()
    placed = []
    for part in ("body", "closure"):
        try:
            path = layout.path("derived", str(record["artifacts"][part]).removeprefix("derived/"))
            fresh = _stat(path) == record["file_stats"][part]
        except Exception:
            return "stale", record, ()
        if not fresh:
            return "stale", record, ()
        placed.append(path)
    return "placed", record, tuple(placed)


# ---------------------------------------------------------------- combine job


def marker_scale(model: Any) -> tuple[float, str, float]:
    """mm per reconstruction unit from the A4 mat markers of the scan's own build."""
    from . import measure_design as md

    workspace = md.find_colmap_workspace(model.path)
    if workspace is None:
        raise ValueError(f"{model.path.name}: no camera workspace for mat-marker scale")
    cameras = md.read_colmap_cameras(workspace[1])
    isolation = md.isolate_object(model, cameras)
    revision = "camera-" + md._sha256_file(workspace[1] / "images.bin")[:40]
    result = md.estimate_marker_scale(model, isolation, cameras, workspace[0], revision)
    return result.mm_per_unit, result.source, result.uncertainty


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, np.floating | np.integer | np.bool_):
        return _jsonable(value.item())
    return value


def _write_atomic(folder: Path, name: str, write: Callable[[Path], bool]) -> Path:
    """Write via ``write(temp)`` then rename to ``<name>-<sha16>.ply`` (immutable artifact)."""
    folder.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{name}-", suffix=".ply", dir=folder)
    os.close(fd)
    try:
        if not write(Path(temporary)):
            raise OSError(f"{name} could not be written")
        target = folder / f"{name}-{_sha256(Path(temporary))[:16]}.ply"
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def write_cloud(folder: Path, part: str, points: np.ndarray, colors: np.ndarray | None) -> Path:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    if colors is not None:
        cloud.colors = o3d.utility.Vector3dVector(colors)
    return _write_atomic(folder, part, lambda path: o3d.io.write_point_cloud(path, cloud))


MESH_METHOD = "open3d_poisson_depth8_outward_normals_bbox_crop_2mm_v2"


def write_mesh(folder: Path, part: str, points: np.ndarray) -> Path:
    """Surface of the merged cloud, so Measure & Design can promote a Scan Master from it."""
    import open3d as o3d

    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(30))
    # ponytail: outward = away from the centroid, then made consistent along the surface;
    # deep recesses (closure underside) may still flip locally. Upgrade: visibility-based.
    cloud.orient_normals_towards_camera_location(points.mean(axis=0))
    cloud.normals = o3d.utility.Vector3dVector(-np.asarray(cloud.normals))
    cloud.orient_normals_consistent_tangent_plane(15)
    mesh, _density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(cloud, depth=8)
    # Fill across unscanned areas is kept (closed surface) and flagged later as coverage
    # gaps by distance to the scanned points (measure_design.derived_surface_gaps); only
    # Poisson's balloon beyond the scanned extent is cut.
    vertices = np.asarray(mesh.vertices)
    low, high = points.min(axis=0) - 2.0, points.max(axis=0) + 2.0
    mesh.remove_vertices_by_mask(((vertices < low) | (vertices > high)).any(axis=1).tolist())
    if len(mesh.triangles) < 20:
        raise OSError("merged part surface could not be meshed")
    return _write_atomic(
        folder, f"{part}-mesh", lambda path: o3d.io.write_triangle_mesh(path, mesh)
    )


class ScenePanel(QWidget):
    """Scene / Objects dock: Closure, Body, Assembled with status and Combine part."""

    part_selected = Signal(object, object)  # part (str | None), tuple[Path, ...] to show
    combine_finished = Signal(str, str)  # part, outcome (combined/refused/cancelled/failed)
    placement_finished = Signal(str)  # outcome (placed/refused/cancelled/failed)

    def __init__(
        self,
        project_manager: ProjectManager,
        job_manager: JobManager,
        entries_provider: Callable[[], list[Any]],
        *,
        scale_for: Callable[[Any], tuple[Any, ...]] = marker_scale,
        aligner: Callable[..., Any] | None = None,
        placer: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("packlab.scene.panel")
        self.projects, self.jobs = project_manager, job_manager
        self.entries_provider = entries_provider
        self.scale_for, self.aligner, self.placer = scale_for, aligner, placer
        self.states: dict[str, PartState] = {}
        # (status none/placed/refused/stale, record, placed body + closure clouds)
        self.placement: tuple[str, dict[str, Any] | None, tuple[Path, ...]] = ("none", None, ())
        self.view: dict[str, Any] = {"part": None, "hidden": []}
        self._jobs_by_part: dict[str, str] = {}
        self._cancel: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._shown: tuple[object, tuple[Path, ...]] | None = None
        self._invoker = MainThreadInvoker()
        self.tree = QTreeWidget()
        self.tree.setObjectName("packlab.scene.tree")
        self.tree.setHeaderLabels([tr("Part"), tr("Status")])
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.itemChanged.connect(self._visibility_changed)
        self.details = QLabel("")
        self.details.setObjectName("packlab.scene.details")
        self.details.setWordWrap(True)
        self.combine_button = QPushButton(tr("Combine part"))
        self.combine_button.setObjectName("packlab.scene.combine")
        self.combine_button.clicked.connect(lambda: self.combine(self.view["part"]))
        self.cancel_button = QPushButton(tr("Cancel combine"))
        self.cancel_button.setObjectName("packlab.scene.cancel")
        self.cancel_button.clicked.connect(lambda: self.cancel(self.view["part"]))
        self.place_button = QPushButton(tr("Place closure on body"))
        self.place_button.setObjectName("packlab.scene.place")
        self.place_button.clicked.connect(self.place)
        buttons = QHBoxLayout()
        buttons.addWidget(self.combine_button)
        buttons.addWidget(self.place_button)
        buttons.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree, 1)
        layout.addLayout(buttons)
        layout.addWidget(self.details)
        self.items: dict[str, QTreeWidgetItem] = {}
        for part in PROJECT_PARTS:
            item = QTreeWidgetItem([tr(PART_LABELS[part]), ""])
            item.setData(0, _ROLE, part)
            self.tree.addTopLevelItem(item)
            self.items[part] = item
        self.projects.add_listener(lambda _metadata: self.refresh())
        self.refresh()

    # ------------------------------------------------------------ state

    def refresh(self) -> None:
        try:
            entries = self.entries_provider() if self.projects.layout is not None else []
            overrides = self.projects.scan_part_roles()
            self.states = part_states(self.projects, entries, overrides)
            self.view = self.projects.part_view()
            self.placement = placement_state(self.projects, self.states)
        except Exception as error:  # unreadable inbox/project: panel stays usable
            self.details.setText(tr("Parts unavailable: {error}").format(error=error))
            self.states, self.view = {}, {"part": None, "hidden": []}
            self.placement = ("none", None, ())
        self.tree.blockSignals(True)
        try:
            assembled = self.items["assembled"]
            assembled.takeChildren()
            for part, item in self.items.items():
                state = self.states.get(part)
                status = (
                    "combining"
                    if part in self._running_parts()
                    else (state.status if state else "missing")
                )
                text = tr(STATUS_TEXT[status])
                if state is not None and state.reason and status in ("single", "refused"):
                    text = f"{text}: {state.reason}"
                item.setText(1, text)
                item.setToolTip(1, text)
                if part != "assembled" and state is not None and state.cloud is not None:
                    child = QTreeWidgetItem([tr(PART_LABELS[part]), tr("shown on Assembled")])
                    child.setData(0, _ROLE, part)
                    child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    hidden = part in self.view["hidden"]
                    child.setCheckState(
                        0, Qt.CheckState.Unchecked if hidden else Qt.CheckState.Checked
                    )
                    assembled.addChild(child)
            assembled.setExpanded(True)
            selected = self.view["part"]
            self.tree.clearSelection()
            if selected in self.items:
                self.tree.setCurrentItem(self.items[selected])
        finally:
            self.tree.blockSignals(False)
        self._update_details()
        self._emit_shown()

    def _running_parts(self) -> set[str]:
        return {part for part, job_id in self._jobs_by_part.items() if self._job_active(job_id)}

    def _job_active(self, job_id: str) -> bool:
        try:
            return self.jobs.get(job_id).state not in TERMINAL_STATES
        except KeyError:
            return False

    def selected_paths(self) -> tuple[Path, ...]:
        part = self.view["part"]
        state = self.states.get(part or "")
        paths = [state.cloud] if state is not None and state.cloud is not None else []
        if part == "assembled":
            status, _record, placed = self.placement
            for index, other in enumerate(("body", "closure")):
                extra = self.states.get(other)
                if other in self.view["hidden"]:
                    continue
                if status == "placed":
                    paths.append(placed[index])  # where the assembled scan puts it
                elif extra and extra.cloud:
                    paths.append(extra.cloud)
        return tuple(paths)

    def selected_cloud(self) -> Path | None:
        """The selected part's own cloud (Measure & Design works on one model)."""
        state = self.states.get(self.view["part"] or "")
        return None if state is None else state.cloud

    def _emit_shown(self) -> None:
        shown = (self.view["part"], self.selected_paths())
        if shown != self._shown:
            self._shown = shown
            self.part_selected.emit(*shown)

    def _update_details(self) -> None:
        part = self.view["part"]
        state = self.states.get(part or "")
        running = part in self._running_parts()
        placing = PLACEMENT in self._running_parts()
        self.combine_button.setEnabled(
            bool(state and state.upright and state.flipped) and not running
        )
        ready = [self.states.get(p) for p in ("assembled", "body", "closure")]
        self.place_button.setEnabled(
            part == "assembled" and not placing and all(s and s.cloud for s in ready)
        )
        self.cancel_button.setEnabled(running or (part == "assembled" and placing))
        if state is None:
            self.details.setText(tr("Select a part to show it in Model Viewer."))
            return
        lines = [f"{tr(PART_LABELS[state.part])}: {tr(STATUS_TEXT[state.status])}"]
        if state.reason:
            lines.append(state.reason)
        record = state.record
        if record and state.status == "combined":
            pair = record["alignments"][-1]
            lines.append(
                tr("coverage {coverage:.0%}, RMSE {rmse:.2f} mm, {points:,} points").format(
                    coverage=pair["coverage"], rmse=pair["rmse_mm"], points=record["point_count"]
                )
            )
            lines.append(tr("Units: mm in the mat frame, METRIC_UNVERIFIED."))
        if part == "assembled":
            lines.extend(self._placement_lines(placing))
        self.details.setText("\n".join(lines))

    def _placement_lines(self, placing: bool) -> list[str]:
        status, record, _placed = self.placement
        if placing:
            return [tr("Placing the closure on the body…")]
        if status == "placed" and record is not None:
            graph = record["graph"]
            body, closure = (item["residuals"] for item in graph["components"])
            pair = graph["diagnostics"]["pair"]
            return [
                tr("Closure placed on body (assembled scan as reference)."),
                tr("body: coverage {coverage:.0%}, RMSE {rmse:.2f} mm").format(
                    coverage=body["coverage"], rmse=body["rmse_mm"]
                ),
                tr("closure: coverage {coverage:.0%}, RMSE {rmse:.2f} mm").format(
                    coverage=closure["coverage"], rmse=closure["rmse_mm"]
                ),
                tr("engaged depth {depth:.1f} mm, clearance {status}").format(
                    depth=graph["relationships"][0]["engaged_depth_mm"], status=pair["status"]
                ),
                tr("Assembly graph {revision}").format(revision=graph["revision_id"][:32]),
                tr("Units: mm in the mat frame, METRIC_UNVERIFIED."),
            ]
        if status == "refused" and record is not None:
            return [tr("Closure placement refused: {reason}").format(reason=record["reason"])]
        if status == "stale":
            return [tr("Parts changed since the closure was placed; place it again.")]
        return [
            tr(
                "Body and closure are shown where their own scans put them; use Place closure "
                "on body to seat the closure using the assembled scan."
            )
        ]

    # ------------------------------------------------------------ owner actions

    def _selection_changed(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]
        part = str(item.data(0, _ROLE)) if item.parent() is None else "assembled"
        self._save_view(part, self.view["hidden"])

    def _visibility_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if item.parent() is None or column != 0:
            return
        part = str(item.data(0, _ROLE))
        hidden = set(self.view["hidden"])
        if item.checkState(0) == Qt.CheckState.Checked:
            hidden.discard(part)
        else:
            hidden.add(part)
        self._save_view("assembled", sorted(hidden))

    def _save_view(self, part: str | None, hidden: list[str]) -> None:
        if self.projects.layout is None:
            return
        try:
            self.projects.set_part_view(part, hidden)
        except Exception as error:
            self.details.setText(tr("Part selection not saved: {error}").format(error=error))
        self.refresh()  # set_part_view notifies only on a new revision

    def cancel(self, part: str | None) -> None:
        for key in (part or "", PLACEMENT if part == "assembled" else ""):
            job_id = self._jobs_by_part.get(key)
            if job_id is not None and self._job_active(job_id):
                self.jobs.request_cancel(job_id)
        self.refresh()

    def combine(self, part: str | None) -> str | None:
        """Start the Combine-part background job for ``part``; returns the job id."""
        state = self.states.get(part or "")
        layout, metadata = self.projects.layout, self.projects.metadata
        if state is None or state.upright is None or state.flipped is None or layout is None:
            return None
        if part in self._running_parts():
            return self._jobs_by_part[str(part)]
        assert metadata is not None
        job = self.jobs.create(
            tr("Combine {part}").format(part=tr(PART_LABELS[state.part])), "part-merge"
        )
        token = threading.Event()
        self._cancel[state.part] = token

        def hook() -> bool:
            token.set()
            return False  # the worker confirms at its next checkpoint

        self.jobs.register_cancel_hook(job.job_id, hook)
        thread = threading.Thread(
            target=self._work,
            args=(job.job_id, state, layout, metadata.project_id, token),
            name=f"packlab-part-{state.part}",
            daemon=True,
        )
        self._jobs_by_part[state.part] = job.job_id
        self._threads[state.part] = thread
        self.jobs.start(job.job_id)
        thread.start()
        self.refresh()
        return job.job_id

    def _work(
        self, job_id: str, state: PartState, layout: Any, project_id: str, token: threading.Event
    ) -> None:
        from packlab_core.multiscan_alignment import (
            METHOD,
            METRIC_STATUS,
            MultiScanAlignmentError,
            ScanInput,
            align_part_pair,
        )

        from . import measure_design as md

        jobs = cast(JobManager, _MainThreadJobs(self.jobs, self._invoker))
        aligner = self.aligner or align_part_pair
        part, root = state.part, layout.root

        def cancelled() -> bool:
            return token.is_set() or jobs.get(job_id).state is JobState.CANCELLED

        written: list[Path] = []

        def finish(outcome: str, record: dict[str, Any] | None = None, error: str = "") -> None:
            self._invoker.call(
                self._finish, job_id, part, outcome, record, error, project_id, written
            )

        try:
            sources, inputs = [], []
            for step, (view, scan) in enumerate(
                (("upright", state.upright), ("flipped", state.flipped))
            ):
                assert scan is not None
                if cancelled():
                    return finish("cancelled")
                jobs.update_progress(
                    job_id, 0.1 + 0.2 * step, tr("Loading {view} scan").format(view=tr(view))
                )
                model = md.load_model(scan.model)
                source: dict[str, Any] = {
                    "view": view,
                    "role": part if view == "upright" else f"{part}_flipped",
                    "package_sha256": scan.package_sha256,
                    "model_path": _rel(root, scan.model),
                    "model_sha256": model.sha256,
                    "mm_per_unit": None,
                    "scale_source": None,
                }
                sources.append(source)
                try:
                    scale = self.scale_for(model)  # (mm_per_unit, source[, uncertainty])
                    source["mm_per_unit"], source["scale_source"] = float(scale[0]), scale[1]
                    source["scale_uncertainty"] = float(scale[2]) if len(scale) > 2 else None
                except ValueError as error:
                    raise MultiScanAlignmentError(
                        f"{view} scan scale unavailable: {error}"
                    ) from error
                inputs.append(
                    ScanInput(
                        f"{part}-{view}-{scan.package_sha256[:12]}",
                        model.points,
                        model.colors,
                        mm_per_unit=float(source["mm_per_unit"]),
                    )
                )
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.5, tr("Aligning upright and upside-down scans"))
            record: dict[str, Any] = {
                "part": part,
                "created_at": datetime.now(UTC).isoformat(),
                "method": METHOD,
                "metric_status": METRIC_STATUS,
                "sources": sources,
                "artifact_path": None,
            }
            try:
                result = aligner(inputs[0], inputs[1])
            except MultiScanAlignmentError as error:
                record.update(status="refused", reason=str(error))
            else:
                if cancelled():
                    return finish("cancelled")
                jobs.update_progress(job_id, 0.9, tr("Writing the merged part cloud"))
                folder = layout.path("derived", "parts")
                target = write_cloud(folder, part, result.points, result.colors)
                written.append(target)
                if cancelled():
                    return finish("cancelled")
                mesh = write_mesh(folder, part, result.points)
                written.append(mesh)
                record.update(
                    status="combined",
                    reason=None,
                    artifact_path=f"derived/parts/{target.name}",
                    file_sha256=_sha256(target),
                    file_stat=_stat(target),
                    mesh_artifact_path=f"derived/parts/{mesh.name}",
                    mesh_sha256=_sha256(mesh),
                    mesh_method=MESH_METHOD,
                    point_count=len(result.points),
                    reference_id=result.reference_id,
                    surface_coverage={k: float(v) for k, v in result.surface_coverage.items()},
                    alignments=[
                        {key: _jsonable(value) for key, value in vars(item).items()}
                        for item in result.alignments
                    ],
                )
            if cancelled():
                return finish("cancelled")
            finish(str(record["status"]), record)
        except MultiScanAlignmentError as error:
            if cancelled():
                return finish("cancelled")
            if not sources:
                return finish("failed", error=str(error))
            finish(
                "refused",
                {
                    "part": part,
                    "status": "refused",
                    "reason": str(error),
                    "created_at": datetime.now(UTC).isoformat(),
                    "method": METHOD,
                    "metric_status": METRIC_STATUS,
                    "sources": sources,
                    "artifact_path": None,
                },
            )
        except Exception as error:  # the job reports it; Studio stays usable
            if cancelled():
                return finish("cancelled")
            finish("failed", error=f"{type(error).__name__}: {error}")

    # ------------------------------------------------------------ closure placement (PL-0484)

    def place(self) -> str | None:
        """Start the Place-closure-on-body background job; returns the job id."""
        layout, metadata = self.projects.layout, self.projects.metadata
        states = {part: self.states.get(part) for part in ("assembled", "body", "closure")}
        if layout is None or any(s is None or s.cloud is None for s in states.values()):
            return None
        if PLACEMENT in self._running_parts():
            return self._jobs_by_part[PLACEMENT]
        assert metadata is not None
        job = self.jobs.create(tr("Place closure on body"), "part-placement")
        token = threading.Event()
        self._cancel[PLACEMENT] = token

        def hook() -> bool:
            token.set()
            return False  # the worker confirms at its next checkpoint

        self.jobs.register_cancel_hook(job.job_id, hook)
        thread = threading.Thread(
            target=self._place_work,
            args=(job.job_id, states, layout, metadata.project_id, token),
            name="packlab-part-placement",
            daemon=True,
        )
        self._jobs_by_part[PLACEMENT] = job.job_id
        self._threads[PLACEMENT] = thread
        self.jobs.start(job.job_id)
        thread.start()
        self.refresh()
        return job.job_id

    def _place_work(
        self,
        job_id: str,
        states: dict[str, PartState],
        layout: Any,
        project_id: str,
        token: threading.Event,
    ) -> None:
        from packlab_core.multiscan_alignment import ScanInput
        from packlab_core.part_placement import (
            METHOD,
            METRIC_STATUS,
            PartInput,
            PartPlacementError,
            part_from_scan,
            place_closure_on_body,
            scan_assembly_graph,
        )

        from . import measure_design as md

        jobs = cast(JobManager, _MainThreadJobs(self.jobs, self._invoker))
        placer = self.placer or place_closure_on_body
        root = layout.root
        written: list[Path] = []
        sources: dict[str, dict[str, Any]] = {}
        record: dict[str, Any] = {
            "created_at": datetime.now(UTC).isoformat(),
            "method": METHOD,
            "metric_status": METRIC_STATUS,
            "sources": sources,
            "artifacts": {},
        }

        def cancelled() -> bool:
            return token.is_set() or jobs.get(job_id).state is JobState.CANCELLED

        def finish(outcome: str, result: dict[str, Any] | None = None, error: str = "") -> None:
            self._invoker.call(
                self._finish, job_id, PLACEMENT, outcome, result, error, project_id, written
            )

        def load(part: str, state: PartState) -> PartInput:
            assert state.cloud is not None
            model = md.load_model(state.cloud)
            source = sources[part]
            source["cloud_sha256"] = model.sha256
            if state.status == "combined":  # already object points in its mat frame, mm
                source.update(frame="part_combine_mat_frame_mm", scale_source="part_combine")
                return PartInput(f"{part}-{model.sha256[:12]}", model.points, model.colors)
            if state.upright is None or state.cloud != state.upright.model:
                raise PartPlacementError(
                    tr("{part}: only the upside-down scan exists; scan it upright").format(
                        part=tr(PART_LABELS[part])
                    ),
                    ("part_missing",),
                )
            try:
                scale = self.scale_for(model)  # (mm_per_unit, source[, uncertainty])
            except ValueError as error:
                raise PartPlacementError(
                    f"{part} scan scale unavailable: {error}", ("scale_unavailable",)
                ) from error
            source.update(
                frame="single_scan_mat_frame_mm",
                mm_per_unit=float(scale[0]),
                scale_source=scale[1],
                scale_uncertainty=float(scale[2]) if len(scale) > 2 else None,
            )
            scan = ScanInput(
                f"{part}-{model.sha256[:12]}", model.points, model.colors, mm_per_unit=scale[0]
            )
            return part_from_scan(scan)

        for part, state in states.items():  # refusals stay matched to the parts they saw
            assert state.cloud is not None
            sources[part] = {
                "status": state.status,
                "cloud_path": _rel(root, state.cloud),
                "scale_key": _scale_key(state),
            }
        try:
            inputs = {}
            for step, part in enumerate(("assembled", "body", "closure")):
                if cancelled():
                    return finish("cancelled")
                label = tr(PART_LABELS[part])
                jobs.update_progress(
                    job_id, 0.1 + 0.15 * step, tr("Loading {part}").format(part=label)
                )
                inputs[part] = load(part, states[part])
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.55, tr("Registering body and closure"))
            result = placer(inputs["assembled"], inputs["body"], inputs["closure"])
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.9, tr("Writing the placed parts"))
            folder = layout.path("derived", "parts")
            stats, outputs = {}, {}
            for part, placement in (("body", result.body), ("closure", result.closure)):
                points = np.asarray(inputs[part].points)
                moved = points @ placement.matrix[:3, :3].T + placement.matrix[:3, 3]
                target = write_cloud(folder, f"{part}-placed", moved, inputs[part].colors)
                written.append(target)
                record["artifacts"][part] = f"derived/parts/{target.name}"
                stats[part] = _stat(target)
                outputs[part] = {
                    "cloud_path": record["artifacts"][part],
                    "cloud_sha256": _sha256(target),
                }
                if cancelled():
                    return finish("cancelled")
            graph = scan_assembly_graph(
                result,
                sources,
                "closure placed on body using the assembled scan (PL-0484)",
                outputs,
            )
            record.update(
                status="placed",
                reason=None,
                file_stats=stats,
                artifact_sha256={part: item["cloud_sha256"] for part, item in outputs.items()},
                graph=graph,
                graph_revision_id=graph["revision_id"],
            )
            finish("placed", record)
        except PartPlacementError as error:
            if cancelled():
                return finish("cancelled")
            record.update(status="refused", reason=str(error), codes=list(error.codes))
            record["artifacts"] = {}
            finish("refused", record)
        except Exception as error:  # the job reports it; Studio stays usable
            if cancelled():
                return finish("cancelled")
            finish("failed", error=f"{type(error).__name__}: {error}")

    def _finish(
        self,
        job_id: str,
        part: str,
        outcome: str,
        record: dict[str, Any] | None,
        error: str,
        project_id: str,
        written: list[Path],
    ) -> None:
        token = self._cancel.get(part)
        placing = part == PLACEMENT
        state = self.jobs.get(job_id).state
        if (token is not None and token.is_set()) or state in (
            JobState.CANCELLING,
            JobState.CANCELLED,
        ):
            outcome, record = "cancelled", None  # a late cancel still discards the result
        metadata = self.projects.metadata
        if record is not None and (metadata is None or metadata.project_id != project_id):
            outcome, error, record = "failed", "project changed while combining", None
        committed = False
        if record is not None:
            try:
                if placing:
                    self.projects.record_part_placement(record)
                else:
                    self.projects.record_part_merge(part, record)
                committed = True
            except Exception as failure:
                outcome, error = "failed", str(failure)
        if not committed:
            self._discard(written)
        if outcome == "cancelled":
            self.jobs.finish_cancel(job_id)
        elif outcome == "failed":
            self.jobs.fail(job_id, error)
        elif self.jobs.get(job_id).state not in TERMINAL_STATES:
            message = (
                tr(STATUS_TEXT.get(outcome, outcome))
                if outcome in ("combined", "placed")
                else tr("refused: {reason}").format(reason=record["reason"] if record else "")
            )
            self.jobs.succeed(job_id, message)
        self.refresh()
        if placing:
            self.placement_finished.emit(outcome)
        else:
            self.combine_finished.emit(part, outcome)

    def _discard(self, written: list[Path]) -> None:
        """Remove files of an uncommitted combine unless a stored record uses them."""
        root = None if self.projects.layout is None else self.projects.layout.root
        kept = {
            str(record.get(key))
            for record in (self.projects.part_merges() if root is not None else {}).values()
            for key in ("artifact_path", "mesh_artifact_path")
        }
        placement = self.projects.part_placement() if root is not None else None
        kept |= {str(path) for path in (placement or {}).get("artifacts", {}).values()}
        for path in written:
            if f"derived/parts/{path.name}" not in kept:
                path.unlink(missing_ok=True)


__all__ = [
    "PartScan",
    "PartState",
    "ScenePanel",
    "marker_scale",
    "part_scans",
    "part_states",
    "placement_state",
]
