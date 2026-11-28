"""Project parts (PL-0485): Closure, Body and Assembled in the Scene / Objects dock.

Each part is built from its upright and upside-down scans (PL-0482 roles). "Combine part"
runs ``align_part_pair`` (PL-0483) on the two dense clouds in a background job and stores
the merged cloud (``derived/parts``), transforms, metrics or the refusal reason in the
project. Merged clouds are in the reference scan's mat frame, mm, METRIC_UNVERIFIED.

"Place closure on body" (PL-0484, on Assembled) registers Body and Closure into the Assembled
cloud (``packlab_core.part_placement``) in a background job and stores the placed clouds
(``derived/parts/*-placed-*.ply``), the scan-level assembly graph revision and clearance
diagnostics, or the typed refusal, in the project.

"Merge interior" (PL-0489, on Body when a body-interior scan exists) aligns the interior scan to
the Body cloud by the rim (``packlab_core.interior_merge``) in a background job and stores the
Body + scanned interior cloud (``derived/parts/body-interior-*.ply``, body points first), depth
coverage per band and provenance, or the typed refusal. Unscanned depth is never filled; the
Body cloud used by Measure & Design is unchanged.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .build_model import MainThreadInvoker, _MainThreadJobs, successful_builds
from .capture_inbox import counted_role, local_time
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
    "merged": "merged",
}
_ROLE = Qt.ItemDataRole.UserRole
OWNER_CONFIRMED = "OWNER_CONFIRMED_UNVERIFIED"  # combine the owner forced on disagreeing scans
ANYWAY = "Combine anyway - I confirm both scans are the same part"
PLACEMENT = "placement"  # job key of the closure-on-body placement
INTERIOR = "interior"  # job key of the body-interior merge


@dataclass(frozen=True)
class PartScan:
    package_sha256: str
    model: Path
    time: float
    revision: str = ""  # reconstruction revision (build) the model comes from


@dataclass(frozen=True)
class PartState:
    part: str
    upright: PartScan | None
    flipped: PartScan | None
    status: str  # see STATUS_TEXT
    reason: str
    cloud: Path | None  # what the viewer shows for this part
    record: dict[str, Any] | None
    interior: PartScan | None = None  # newest body-interior scan (Body only)


def part_scans(
    entries: list[Any],
    overrides: dict[str, str],
    project_root: Path | None,
    choices: dict[str, str] | None = None,
) -> dict[str, dict[str, PartScan]]:
    """Build per part view (upright / flipped / interior): the owner's chosen successful build
    of the scan (``choices``: digest -> revision), else its newest successful one; newest scan
    per view wins."""
    builds = successful_builds(project_root)
    found: dict[str, dict[str, PartScan]] = {part: {} for part in PROJECT_PARTS}
    newest: dict[tuple[str, str], float] = {}  # (part, view) -> newest build time of its scan
    for entry in entries:
        role = counted_role(entry, overrides, set(builds))
        options = builds.get(entry.package_sha256)
        if role is None or not options:
            continue
        part, _, view = role.partition("_")
        if part not in found or view not in ("", "flipped", "interior"):
            continue
        view = view or "upright"
        chosen = (choices or {}).get(entry.package_sha256)
        build = next((b for b in options if b["revision"] == chosen), options[0])
        scan = PartScan(
            entry.package_sha256, Path(build["model"]), float(build["time"]), build["revision"]
        )
        if newest.get((part, view), -1.0) < options[0]["time"]:
            newest[part, view] = options[0]["time"]
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
    scans = part_scans(entries, overrides, root, manager.scan_builds())
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
    for part, scans_of_part in scans.items():
        if "interior" in scans_of_part:
            states[part] = replace(states[part], interior=scans_of_part["interior"])
    return states


def owner_confirmed(record: dict[str, Any] | None) -> bool:
    """Is this Combine record an owner-confirmed (unverified) merge of disagreeing scans?"""
    return bool(record) and record.get("verification") == OWNER_CONFIRMED  # type: ignore[union-attr]


def disagreement_lines(record: dict[str, Any] | None) -> list[str]:
    """The measured disagreements of a refusal the owner may override, or of an owner-confirmed
    merge, in plain words."""
    from packlab_core.multiscan_alignment import disagreement_text

    items = (record or {}).get("disagreements") or (record or {}).get("override") or []
    return [f"- {disagreement_text(item)}" for item in items if isinstance(item, dict)]


def _default_confirm(parent: QWidget, text: str) -> bool:
    answer = QMessageBox.question(
        parent,
        tr("Combine anyway?"),
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return answer == QMessageBox.StandardButton.Yes


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


def interior_state(
    manager: ProjectManager, states: dict[str, PartState]
) -> tuple[str, dict[str, Any] | None, Path | None]:
    """(none / merged / refused / stale, record, merged Body + interior cloud).

    Stale when the Body cloud (path, digest, status, combine scale) or the newest body-interior
    scan differs from what the merge used, or the merged cloud is missing or changed on disk.
    """
    layout, record = manager.layout, manager.interior_merge()
    body = states.get("body")
    if layout is None or record is None:
        return "none", None, None
    sources = record.get("sources") or {}
    stored, scan = sources.get("body") or {}, sources.get("interior") or {}
    if (
        body is None
        or body.cloud is None
        or body.interior is None
        or stored.get("cloud_path") != _rel(layout.root, body.cloud)
        or stored.get("status") != body.status
        or stored.get("scale_key") != _scale_key(body)
        or stored.get("cloud_sha256") != _cached_sha(body.cloud)
        or scan.get("package_sha256") != body.interior.package_sha256
        or scan.get("model_path") != _rel(layout.root, body.interior.model)
    ):
        return "stale", record, None
    if record.get("status") != "merged":
        return "refused", record, None
    try:
        path = layout.path("derived", str(record["artifact_path"]).removeprefix("derived/"))
        fresh = _stat(path) == record["file_stat"]
    except Exception:
        return "stale", record, None
    return ("merged", record, path) if fresh else ("stale", record, None)


def depth_ranges(bands: list[dict[str, Any]], key: str) -> str:
    """'2-60, 64-70' from consecutive bands where ``bands[i][key]`` is true (depth in mm)."""
    ranges: list[list[float]] = []
    for band in bands:
        if not band[key]:
            continue
        if ranges and abs(ranges[-1][1] - band["top_mm"]) < 1e-6:
            ranges[-1][1] = band["bottom_mm"]
        else:
            ranges.append([band["top_mm"], band["bottom_mm"]])
    return ", ".join(f"{top:.0f}-{bottom:.0f}" for top, bottom in ranges)


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
    # Poisson can emit zero-area slivers (coincident vertices), which the Scan Master geometry
    # statistics reject: merge duplicates and drop zero-area triangles.
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    v, t = np.asarray(mesh.vertices), np.asarray(mesh.triangles)
    area = np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1)
    mesh.remove_triangles_by_mask((area <= 1e-9).tolist())
    mesh.remove_unreferenced_vertices()
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
    interior_finished = Signal(str)  # outcome (merged/refused/cancelled/failed)

    def __init__(
        self,
        project_manager: ProjectManager,
        job_manager: JobManager,
        entries_provider: Callable[[], list[Any]],
        *,
        scale_for: Callable[[Any], tuple[Any, ...]] = marker_scale,
        aligner: Callable[..., Any] | None = None,
        placer: Callable[..., Any] | None = None,
        interior_merger: Callable[..., Any] | None = None,
        confirm: Callable[[QWidget, str], bool] = _default_confirm,
    ) -> None:
        super().__init__()
        self.confirm = confirm
        self.setObjectName("packlab.scene.panel")
        self.projects, self.jobs = project_manager, job_manager
        self.entries_provider = entries_provider
        self.scale_for, self.aligner, self.placer = scale_for, aligner, placer
        self.interior_merger = interior_merger
        # (status none/merged/refused/stale, record, merged Body + interior cloud)
        self.interior: tuple[str, dict[str, Any] | None, Path | None] = ("none", None, None)
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
        self.anyway_button = QPushButton(tr(ANYWAY))
        self.anyway_button.setObjectName("packlab.scene.combine_anyway")
        self.anyway_button.clicked.connect(lambda: self.combine_anyway(self.view["part"]))
        self.cancel_button = QPushButton(tr("Cancel combine"))
        self.cancel_button.setObjectName("packlab.scene.cancel")
        self.cancel_button.clicked.connect(lambda: self.cancel(self.view["part"]))
        self.place_button = QPushButton(tr("Place closure on body"))
        self.place_button.setObjectName("packlab.scene.place")
        self.place_button.clicked.connect(self.place)
        self.interior_button = QPushButton(tr("Merge interior"))
        self.interior_button.setObjectName("packlab.scene.interior")
        self.interior_button.clicked.connect(self.merge_interior)
        # Which successful build of each scan feeds the part (default: the latest).
        self.build_boxes: dict[str, QComboBox] = {}
        builds_form = QFormLayout()
        for view, label in (("upright", "Upright build"), ("flipped", "Upside-down build")):
            box = QComboBox()
            box.setObjectName(f"packlab.scene.build.{view}")
            box.activated.connect(lambda index, view=view: self._choose_build(view, index))
            builds_form.addRow(tr(label), box)
            self.build_boxes[view] = box
        self.builds: dict[str, list[dict[str, Any]]] = {}
        self.build_notice = ""
        buttons = QHBoxLayout()
        buttons.addWidget(self.combine_button)
        buttons.addWidget(self.place_button)
        buttons.addWidget(self.interior_button)
        buttons.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree, 1)
        layout.addLayout(builds_form)
        layout.addLayout(buttons)
        layout.addWidget(self.anyway_button)
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
            layout = self.projects.layout
            self.builds = successful_builds(None if layout is None else layout.root)
            self._repair_build_choices()
            self.view = self.projects.part_view()
            self.placement = placement_state(self.projects, self.states)
            self.interior = interior_state(self.projects, self.states)
        except Exception as error:  # unreadable inbox/project: panel stays usable
            self.details.setText(tr("Parts unavailable: {error}").format(error=error))
            self.states, self.view, self.builds = {}, {"part": None, "hidden": []}, {}
            self.placement = ("none", None, ())
            self.interior = ("none", None, None)
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
                if status == "combined" and state is not None and owner_confirmed(state.record):
                    text = tr("combined - owner-confirmed, UNVERIFIED")
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
        if part == "body" and self.interior[0] == "merged":
            paths = [cast(Path, self.interior[2])]  # Body + scanned interior
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
        offer = bool(state and state.status == "refused" and (state.record or {}).get("override"))
        self.anyway_button.setVisible(offer)
        self.anyway_button.setEnabled(offer and not running)
        ready = [self.states.get(p) for p in ("assembled", "body", "closure")]
        self.place_button.setEnabled(
            part == "assembled" and not placing and all(s and s.cloud for s in ready)
        )
        merging = INTERIOR in self._running_parts()
        self.interior_button.setVisible(bool(part == "body" and state and state.interior))
        self.interior_button.setEnabled(bool(state and state.cloud) and not merging)
        self.cancel_button.setEnabled(
            running or (part == "assembled" and placing) or (part == "body" and merging)
        )
        self._update_builds(state, running)
        if state is None:
            self.details.setText(tr("Select a part to show it in Model Viewer."))
            return
        lines = [f"{tr(PART_LABELS[state.part])}: {tr(STATUS_TEXT[state.status])}"]
        if self.build_notice:
            lines.append(self.build_notice)
        if state.reason:
            lines.append(state.reason)
        record = state.record
        if record and state.status == "refused" and record.get("override_refused"):
            lines.append(
                tr("Combine anyway is not offered: {reason}.").format(
                    reason=record["override_refused"]
                )
            )
        if record and state.status == "refused" and record.get("override"):
            lines.append(tr("The two scans disagree, measured:"))
            lines.extend(disagreement_lines(record))
            lines.append(tr("Only if both scans are certainly the same part: use Combine anyway."))
        if record and state.status == "combined" and owner_confirmed(record):
            lines.append(
                tr(
                    "OWNER_CONFIRMED_UNVERIFIED: combined on the owner's confirmation "
                    "({time}); the scans disagree:"
                ).format(time=record.get("owner_confirmed_at", ""))
            )
            lines.extend(disagreement_lines(record))
        if record and state.status == "combined":
            pair = record["alignments"][-1]
            lines.append(
                tr("coverage {coverage:.0%}, RMSE {rmse:.2f} mm, {points:,} points").format(
                    coverage=pair["coverage"], rmse=pair["rmse_mm"], points=record["point_count"]
                )
            )
            lines.extend(pair.get("limitations") or [])
            lines.append(tr("Units: mm in the mat frame, METRIC_UNVERIFIED."))
        if part == "assembled":
            lines.extend(self._placement_lines(placing))
        if part == "body" and state.interior is not None:
            lines.extend(self._interior_lines(merging))
        self.details.setText("\n".join(lines))

    def _heights(self) -> dict[str, float]:
        """Own mat-frame height per model path, as measured by stored combines."""
        return {
            str(source["model_path"]): float(source["height_mm"])
            for record in self.projects.part_merges().values()
            for source in record.get("sources", [])
            if isinstance(source, dict) and isinstance(source.get("height_mm"), (int, float))
        }

    def _update_builds(self, state: PartState | None, running: bool) -> None:
        root = None if self.projects.layout is None else self.projects.layout.root
        heights = self._heights() if root is not None else {}
        for view, box in self.build_boxes.items():
            scan = None if state is None else getattr(state, view)
            options = [] if scan is None else self.builds.get(scan.package_sha256, [])
            box.clear()
            for index, build in enumerate(options):
                preset = {"fast": tr("Fast"), "high": tr("High quality")}.get(
                    build["preset"], tr("build")
                )
                text = f"{preset} · {local_time(build['time'])}"
                height = heights.get(_rel(root, build["model"])) if root is not None else None
                if height is not None:
                    text += f" · {height:.1f} mm"
                if index == 0:
                    text = tr("latest: {build}").format(build=text)
                box.addItem(text, build["revision"])
            if scan is not None:
                box.setCurrentIndex(max(0, box.findData(scan.revision)))
            box.setEnabled(len(options) > 1 and not running)

    def _repair_build_choices(self) -> None:
        """A chosen build that no longer exists (deleted / failed rebuild): say so, clear it."""
        for digest, revision in self.projects.scan_builds().items():
            if revision not in {build["revision"] for build in self.builds.get(digest, [])}:
                self.build_notice = tr(
                    "Selected build {revision} is missing; using the latest build."
                ).format(revision=revision[:10])
                try:
                    self.projects.set_scan_build(digest, None)
                except Exception as error:
                    self.build_notice = tr("Build choice not saved: {error}").format(error=error)

    def _choose_build(self, view: str, index: int) -> None:
        state = self.states.get(self.view["part"] or "")
        scan = None if state is None else getattr(state, view)
        if scan is None or self.projects.layout is None:
            return
        revision = self.build_boxes[view].itemData(index)
        latest = index == 0  # the newest build: follow future builds too
        self.build_notice = ""
        try:
            self.projects.set_scan_build(scan.package_sha256, None if latest else revision)
        except Exception as error:
            self.details.setText(tr("Build choice not saved: {error}").format(error=error))
        self.refresh()

    def _interior_lines(self, merging: bool) -> list[str]:
        status, record, _path = self.interior
        if merging:
            return [tr("Merging the body interior…")]
        body = self.states.get("body")
        if body is not None and owner_confirmed(body.record):
            badge = [
                tr("OWNER_CONFIRMED_UNVERIFIED Body: the interior sits on an unverified Body.")
            ]
            return badge + self._interior_lines_inner(status, record)
        return self._interior_lines_inner(status, record)

    def _interior_lines_inner(self, status: str, record: dict[str, Any] | None) -> list[str]:
        if status == "merged" and record is not None:
            lines = [
                tr("Interior merged (rim alignment, overlap {overlap:.0%}).").format(
                    overlap=record["rim_overlap"]
                ),
                tr(
                    "Interior scanned to {depth:.0f} mm below the rim (rim {rim:.0f} mm above "
                    "the mat), wall about {wall:.1f} mm."
                ).format(
                    depth=record["deepest_covered_mm"],
                    rim=record["interior_depth_mm"],
                    wall=record.get("wall_mm") or 0.0,
                ),
            ]
            if record.get("floor_depth_mm") is not None:
                lines.append(
                    tr("Inner floor at {floor:.0f} mm below the rim; below it is the base.").format(
                        floor=record["floor_depth_mm"]
                    )
                )
            missing = depth_ranges(record["bands"], "missing")
            if missing:
                lines.append(
                    tr("Not scanned (not filled): {ranges} mm depth.").format(ranges=missing)
                )
            lines.append(tr("Units: mm in the mat frame, METRIC_UNVERIFIED."))
            return lines
        if status == "refused" and record is not None:
            return [tr("Interior merge refused: {reason}").format(reason=record["reason"])]
        if status == "stale":
            return [tr("Body or interior scan changed since the merge; merge again.")]
        return [tr("Body interior scan present: use Merge interior.")]

    def _placement_lines(self, placing: bool) -> list[str]:
        status, record, _placed = self.placement
        if placing:
            return [tr("Placing the closure on the body…")]
        unverified = [
            tr(PART_LABELS[part])
            for part, source in ((record or {}).get("sources") or {}).items()
            if isinstance(source, dict) and source.get("verification") == OWNER_CONFIRMED
        ]
        if status == "placed" and record is not None and unverified:
            lines = [
                tr("OWNER_CONFIRMED_UNVERIFIED parts in this placement: {parts}").format(
                    parts=", ".join(unverified)
                )
            ]
            return lines + self._placement_lines_inner(status, record, placing)
        return self._placement_lines_inner(status, record, placing)

    def _placement_lines_inner(
        self, status: str, record: dict[str, Any] | None, placing: bool
    ) -> list[str]:
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
        extra = {"assembled": PLACEMENT, "body": INTERIOR}.get(part or "", "")
        for key in (part or "", extra):
            job_id = self._jobs_by_part.get(key)
            if job_id is not None and self._job_active(job_id):
                self.jobs.request_cancel(job_id)
        self.refresh()

    def combine_anyway(self, part: str | None) -> str | None:
        """Ask the owner to confirm both scans are the same part, then combine overriding the
        agreement gates (offered only for such refusals)."""
        state = self.states.get(part or "")
        if state is None or state.status != "refused" or not (state.record or {}).get("override"):
            return None
        text = "\n".join(
            [
                tr("The automatic check refused this pair. The two scans disagree, measured:"),
                *disagreement_lines(state.record),
                "",
                tr(
                    "Combine anyway takes the upper part from the upright scan and the base from "
                    "the upside-down scan, blended where their walls agree best. The result is "
                    "marked OWNER_CONFIRMED_UNVERIFIED and METRIC_UNVERIFIED; it is never treated "
                    "as verified."
                ),
                "",
                tr("Confirm that both scans show the same part?"),
            ]
        )
        if not self.confirm(self, text):
            return None
        return self.combine(part, confirm=True)

    def combine(self, part: str | None, confirm: bool = False) -> str | None:
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
            args=(job.job_id, state, layout, metadata.project_id, token, confirm),
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
        self,
        job_id: str,
        state: PartState,
        layout: Any,
        project_id: str,
        token: threading.Event,
        confirm: bool = False,
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
                        # standard uncertainty mm/unit -> relative (bounds the scale check)
                        scale_uncertainty=(
                            None
                            if source["scale_uncertainty"] is None
                            else min(0.099, source["scale_uncertainty"] / source["mm_per_unit"])
                        ),
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
                if confirm:
                    confirmed_at = datetime.now(UTC).isoformat()
                    result = aligner(inputs[0], inputs[1], owner_confirmed=True)
                else:
                    result = aligner(inputs[0], inputs[1])
            except MultiScanAlignmentError as error:
                record.update(status="refused", reason=str(error))
                offer = getattr(error, "override_disagreements", None)
                refusal = getattr(error, "override_refusal", None)
                if refusal:
                    record["override_refused"] = str(refusal)
                if offer:
                    record["override"] = [
                        {key: _jsonable(value) for key, value in item.items()} for item in offer
                    ]
                heights = getattr(error, "heights_mm", None) or {}
                for source, item in zip(sources, inputs, strict=True):
                    if item.scan_id in heights:
                        source["height_mm"] = float(heights[item.scan_id])
            else:
                for source, item in zip(sources, result.alignments, strict=False):
                    height = getattr(item, "height_mm", float("nan"))
                    if np.isfinite(height):
                        source["height_mm"] = float(height)
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
                verification = str(getattr(result, "verification", "GATE_PASSED"))
                record["verification"] = verification
                if verification == OWNER_CONFIRMED:
                    record.update(
                        owner_confirmed_at=confirmed_at,
                        confirmation="owner confirmed both scans are the same part",
                        disagreements=[
                            {key: _jsonable(value) for key, value in item.items()}
                            for item in result.disagreements
                        ],
                    )
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
        from packlab_core.part_placement import (
            METHOD,
            METRIC_STATUS,
            PartInput,
            PartPlacementError,
            place_closure_on_body,
            scan_assembly_graph,
        )

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
            return cast(PartInput, self._part_input(part, state, sources[part]))

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

    def _part_input(
        self, part: str, state: PartState, source: dict[str, Any], *, upright_only: bool = True
    ) -> Any:
        """PartInput for a part's cloud (combined: as is; single scan: marker scale + mat
        frame); records frame / scale provenance in ``source``. Raises PartPlacementError."""
        from packlab_core.multiscan_alignment import ScanInput
        from packlab_core.part_placement import PartInput, PartPlacementError, part_from_scan

        from . import measure_design as md

        assert state.cloud is not None
        model = md.load_model(state.cloud)
        source["cloud_sha256"] = model.sha256
        if state.status == "combined":  # already object points in its mat frame, mm
            source.update(frame="part_combine_mat_frame_mm", scale_source="part_combine")
            if owner_confirmed(state.record):
                source["verification"] = OWNER_CONFIRMED
            return PartInput(f"{part}-{model.sha256[:12]}", model.points, model.colors)
        if upright_only and (state.upright is None or state.cloud != state.upright.model):
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

    # ------------------------------------------------------------ body interior (PL-0489)

    def merge_interior(self) -> str | None:
        """Start the Merge-interior background job on Body; returns the job id."""
        layout, metadata = self.projects.layout, self.projects.metadata
        body = self.states.get("body")
        if layout is None or body is None or body.cloud is None or body.interior is None:
            return None
        if INTERIOR in self._running_parts():
            return self._jobs_by_part[INTERIOR]
        assert metadata is not None
        job = self.jobs.create(tr("Merge interior"), "interior-merge")
        token = threading.Event()
        self._cancel[INTERIOR] = token

        def hook() -> bool:
            token.set()
            return False  # the worker confirms at its next checkpoint

        self.jobs.register_cancel_hook(job.job_id, hook)
        thread = threading.Thread(
            target=self._interior_work,
            args=(job.job_id, body, layout, metadata.project_id, token),
            name="packlab-interior-merge",
            daemon=True,
        )
        self._jobs_by_part[INTERIOR] = job.job_id
        self._threads[INTERIOR] = thread
        self.jobs.start(job.job_id)
        thread.start()
        self.refresh()
        return job.job_id

    def _interior_work(
        self, job_id: str, body: PartState, layout: Any, project_id: str, token: threading.Event
    ) -> None:
        from packlab_core.interior_merge import METHOD, METRIC_STATUS, InteriorMergeError
        from packlab_core.interior_merge import merge_interior as core_merge
        from packlab_core.part_placement import PartPlacementError

        jobs = cast(JobManager, _MainThreadJobs(self.jobs, self._invoker))
        merger = self.interior_merger or core_merge
        root = layout.root
        written: list[Path] = []
        assert body.cloud is not None and body.interior is not None
        interior_scan = body.interior
        sources: dict[str, dict[str, Any]] = {
            "body": {
                "status": body.status,
                "cloud_path": _rel(root, body.cloud),
                "scale_key": _scale_key(body),
                **({"verification": OWNER_CONFIRMED} if owner_confirmed(body.record) else {}),
            },
            "interior": {
                "role": "body_interior",
                "package_sha256": interior_scan.package_sha256,
                "model_path": _rel(root, interior_scan.model),
            },
        }
        record: dict[str, Any] = {
            "created_at": datetime.now(UTC).isoformat(),
            "method": METHOD,
            "metric_status": METRIC_STATUS,
            "sources": sources,
            "artifact_path": None,
        }

        def cancelled() -> bool:
            return token.is_set() or jobs.get(job_id).state is JobState.CANCELLED

        def finish(outcome: str, result: dict[str, Any] | None = None, error: str = "") -> None:
            self._invoker.call(
                self._finish, job_id, INTERIOR, outcome, result, error, project_id, written
            )

        try:
            jobs.update_progress(job_id, 0.1, tr("Loading {part}").format(part=tr("Body")))
            body_input = self._part_input("body", body, sources["body"])
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.3, tr("Loading the interior scan"))
            scan_state = PartState("body", None, None, "single", "", interior_scan.model, None)
            interior_input = self._part_input(
                "body-interior", scan_state, sources["interior"], upright_only=False
            )
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.55, tr("Aligning the interior by the rim"))
            result = merger(body_input, interior_input)
            if cancelled():
                return finish("cancelled")
            jobs.update_progress(job_id, 0.9, tr("Writing the body with its interior"))
            folder = layout.path("derived", "parts")
            target = write_cloud(folder, "body-interior", result.points, result.colors)
            written.append(target)
            if cancelled():
                return finish("cancelled")
            counts = np.bincount(result.source_index, minlength=2)
            record.update(
                status="merged",
                reason=None,
                artifact_path=f"derived/parts/{target.name}",
                file_sha256=_sha256(target),
                file_stat=_stat(target),
                point_order="body_points_then_interior_points",
                point_counts={"body": int(counts[0]), "interior": int(counts[1])},
                source_ids=list(result.source_ids),
                matrix=_jsonable(result.matrix),
                rim={k: float(v) for k, v in result.rim.items()},
                rim_overlap=float(result.rim_overlap),
                rmse_mm=_jsonable(float(result.rmse_mm)),
                yaw_determined=bool(result.yaw_determined),
                reachability={k: _jsonable(v) for k, v in vars(result.reachability).items()},
                interior_depth_mm=float(result.reachability.depth_mm),
                deepest_covered_mm=float(result.deepest_covered_mm),
                bands=[
                    {
                        "top_mm": band.top_mm,
                        "bottom_mm": band.bottom_mm,
                        "coverage": band.coverage,
                        "points": band.points,
                        "kind": band.kind,  # covered / missing / base (under the floor)
                        "missing": band.kind == "missing",
                    }
                    for band in result.bands
                ],
                missing=[list(item) for item in result.missing],
                wall_mm=_jsonable(float(result.wall_mm)),
                wall_noise_mm=_jsonable(float(result.wall_noise_mm)),
                floor_depth_mm=result.floor_depth_mm,
                interior_provenance=result.interior_provenance,
                unscanned_depth_filled=False,
                body_design_model_affected=False,
            )
            finish("merged", record)
        except (InteriorMergeError, PartPlacementError) as error:
            if cancelled():
                return finish("cancelled")
            record.update(status="refused", reason=str(error), codes=list(error.codes))
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
        placing, interior = part == PLACEMENT, part == INTERIOR
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
        previous = self.projects.interior_merge() if interior and record is not None else None
        if record is not None:
            try:
                if placing:
                    self.projects.record_part_placement(record)
                elif interior:
                    self.projects.record_interior_merge(record)
                else:
                    self.projects.record_part_merge(part, record)
                committed = True
            except Exception as failure:
                outcome, error = "failed", str(failure)
        if not committed:
            self._discard(written)
        elif previous and previous.get("artifact_path") and self.projects.layout is not None:
            old = str(previous["artifact_path"]).removeprefix("derived/")
            self._discard([self.projects.layout.path("derived", old)])  # replaced: orphaned
        if outcome == "cancelled":
            self.jobs.finish_cancel(job_id)
        elif outcome == "failed":
            self.jobs.fail(job_id, error)
        elif self.jobs.get(job_id).state not in TERMINAL_STATES:
            if outcome in ("combined", "placed", "merged"):
                self.jobs.succeed(job_id, tr(STATUS_TEXT.get(outcome, outcome)))
            else:  # a refusal is no success: the Jobs list must not show "[succeeded] 100%"
                reason = record["reason"] if record else ""
                refused = tr("refused: {reason}").format(reason=reason)
                self.jobs.fail(job_id, refused, message=refused)
        self.refresh()
        if placing:
            self.placement_finished.emit(outcome)
        elif interior:
            self.interior_finished.emit(outcome)
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
        merged = self.projects.interior_merge() if root is not None else None
        kept.add(str((merged or {}).get("artifact_path")))
        for path in written:
            if f"derived/parts/{path.name}" not in kept:
                path.unlink(missing_ok=True)


__all__ = [
    "PartScan",
    "PartState",
    "ScenePanel",
    "depth_ranges",
    "interior_state",
    "disagreement_lines",
    "marker_scale",
    "owner_confirmed",
    "part_scans",
    "part_states",
    "placement_state",
]
