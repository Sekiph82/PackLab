from __future__ import annotations

from packlab_studio.app import create_application
from packlab_studio.shell import StudioMainWindow
from packlab_studio.workspace import DockId, WorkspaceName


def test_default_dock_inventory_and_stable_object_names(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-workspace-test"])
    window = StudioMainWindow()
    window.show()
    app.processEvents()
    assert set(window.workspace.docks) == set(DockId)
    assert {dock.objectName() for dock in window.workspace.docks.values()} == {item.value for item in DockId}
    assert len(window.findChildren(type(next(iter(window.workspace.docks.values()))))) == len(DockId)
    window.close()
    app.processEvents()


def test_show_hide_move_and_deterministic_reset(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-workspace-state-test"])
    window = StudioMainWindow()
    window.show()
    app.processEvents()
    scene = window.workspace.docks[DockId.SCENE]
    scene.hide()
    window.workspace.reset_to_default(WorkspaceName.SETTINGS)
    assert not scene.isVisible()
    assert window.workspace.docks[DockId.PROPERTIES].isVisible()
    window.workspace.reset_to_default(WorkspaceName.LIBRARY)
    assert scene.isVisible()
    assert not window.workspace.docks[DockId.LOGS].isVisible()
    assert window.workspace.docks[DockId.SCENE].objectName() == DockId.SCENE.value
    window.close()
    app.processEvents()
