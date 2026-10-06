# ruff: noqa: F821
# Deterministic one-directory production build. Dynamic native boundaries are explicit.
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, copy_metadata

root = Path(SPECPATH).parents[1]
entry = root / "tools" / "packaging" / "packlab_studio_entry.py"
qt_contract = root / "tools" / "packaging" / "qt_module_contract.json"
provenance = Path(__import__("os").environ["PACKLAB_PROVENANCE_PATH"])
schema_path = root / "schemas"
branding_path = root / "apps" / "windows-studio" / "assets" / "branding"
icon_path = branding_path / "PackLab.ico"
dist_path = Path(__import__("os").environ["PACKLAB_STAGE_PATH"])
work_path = Path(__import__("os").environ["PACKLAB_WORK_PATH"])


ocp_imports = [
    "OCP",
    "OCP.Bnd",
    "OCP.BRep",
    "OCP.BRepAdaptor",
    "OCP.BRepAlgoAPI",
    "OCP.BRepBndLib",
    "OCP.BRepBuilderAPI",
    "OCP.BRepCheck",
    "OCP.BRepClass",
    "OCP.BRepLProp",
    "OCP.BRepMesh",
    "OCP.BRepOffsetAPI",
    "OCP.BRepPrimAPI",
    "OCP.BRepTools",
    "OCP.GeomAbs",
    "OCP.gp",
    "OCP.HLRAlgo",
    "OCP.HLRBRep",
    "OCP.IFSelect",
    "OCP.Interface",
    "OCP.STEPControl",
    "OCP.StlAPI",
    "OCP.TColStd",
    "OCP.TopAbs",
    "OCP.TopExp",
    "OCP.TopLoc",
    "OCP.TopoDS",
    "OCP.TopTools",
]
open3d_imports = [
    "open3d",
    "open3d._build_config",
    "open3d.pybind",
    "open3d.visualization",
    "open3d.ml",
]
open3d_native = [
    item
    for item in collect_dynamic_libs("open3d")
    if Path(item[0]).name.casefold() not in {"open3d_torch_ops.dll"}
]

analysis = Analysis(
    [str(entry)],
    pathex=[str(root / "core" / "src"), str(root / "apps" / "windows-studio" / "src")],
    binaries=open3d_native,
    datas=[
        (str(provenance), "."),
        (str(schema_path), "schemas"),
        (str(branding_path), "apps/windows-studio/assets/branding"),
        *copy_metadata("cadquery-ocp-novtk"),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtSvg",
        "PySide6.QtPdf",
        "OCP",
        "open3d",
        *ocp_imports,
        *open3d_imports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Open3D's package initializer references optional notebook and test helpers.
    # PackLab's adapter does not use them; the frozen geometry round trip verifies
    # the exact retained Open3D runtime remains complete.
    excludes=["PySide6.QtVirtualKeyboard", "IPython", "jedi", "nbformat", "pytest"],
    noarchive=False,
    optimize=0,
)


def keep_curated_qt_file(destination):
    normalized = destination.replace("\\", "/").casefold()
    if "pyside6" in normalized.split("/"):
        parts = normalized.split("/")
        package_index = parts.index("pyside6")
        if parts[package_index + 1 : package_index + 2] == ["plugins"]:
            plugin = "/".join(parts[package_index + 2 :])
            return plugin in {
                item.casefold()
                for item in __import__("json").loads(qt_contract.read_text())["plugin_allowlist"]
            }
        tail = "/".join(parts[parts.index("pyside6") + 1 :])
        if tail.endswith(".pyd"):
            module = Path(tail).stem.casefold()
            return module in {"qtcore", "qtgui", "qtwidgets", "qtsvg", "qtpdf", "qtnetwork"}
        if tail.endswith(".qm") or "/translations/" in tail:
            return False
    base = Path(normalized).name
    # Qt resolves its Windows ICU dependency from the OS. Prevent PyInstaller
    # from collecting unrelated ICU DLLs from the build machine's PATH (for
    # example, Codex's Poppler ICU 78, which is incompatible with this Qt build).
    if base.startswith("icu") and base.endswith(".dll"):
        return False
    if base.startswith("qt6") and base.endswith(".dll"):
        native_allowlist = {
            item.casefold()
            for item in __import__("json").loads(qt_contract.read_text())["native_module_dlls"]
        }
        return base in native_allowlist
    return True


analysis.binaries = [item for item in analysis.binaries if keep_curated_qt_file(item[0])]
analysis.datas = [item for item in analysis.datas if keep_curated_qt_file(item[0])]

pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="PackLabStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path),
)
collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="PackLabStudio",
    distpath=str(dist_path),
    workpath=str(work_path),
)
