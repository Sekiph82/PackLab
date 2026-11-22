"""PL-0487 review V02: the shared artwork orientation works without source files.

The packaged Studio ships only .pyc files, so nothing on the import path may need
``inspect.getsource``; the Blender runner and the Studio preview run the same source text.
"""

from __future__ import annotations

import compileall
import shutil
import subprocess
import sys
from pathlib import Path

import packlab_core
from packlab_core import blender_scene_package as package

CHECK = """
import sys
sys.path.insert(0, sys.argv[1])
import inspect

def refuse(*_args, **_kwargs):
    raise OSError("no source in a packaged build")

inspect.getsource = refuse
from packlab_core import blender_scene_package as package
assert package.__file__.endswith(".pyc"), package.__file__
overlay = {
    "mapping_mode": "CYLINDRICAL_WRAP",
    "geometry": {
        "angular_start_radians": 2.5, "angular_end_radians": 3.8,
        "azimuth_direction": "+Y_TO_PLUS_X", "axis": [0.0, 0.0, 1.0],
        "axial_start_mm_unverified": 5.0, "axial_end_mm_unverified": 45.0,
    },
}
namespace = {}
exec(package.VIEWER_ORIENTATION_SOURCE, namespace)
runner = package.BLENDER_SCENE_RUNNER
assert package.VIEWER_ORIENTATION_SOURCE in runner and "__PACKLAB" not in runner
assert package.artwork_viewer_orientation(overlay) == namespace["_viewer_orientation"](overlay)
print(package.artwork_viewer_orientation(overlay))
"""


def test_orientation_imports_from_pyc_only_package_and_matches_blender(tmp_path) -> None:
    # Same layout as the repo/bundle: core/src/packlab_core next to the data it reads.
    source = Path(packlab_core.__file__).parent
    copy = tmp_path / "core" / "src" / "packlab_core"
    shutil.copytree(source, copy)
    shutil.copytree(source.parents[2] / "schemas", tmp_path / "schemas")
    assert compileall.compile_dir(copy, legacy=True, quiet=1)
    for module in copy.rglob("*.py"):
        module.unlink()
    shutil.rmtree(copy / "__pycache__", ignore_errors=True)
    result = subprocess.run(
        [sys.executable, "-c", CHECK, str(copy.parent)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "(True, True)"  # back-facing wrap: u runs to the left


def test_runner_embeds_exactly_the_shared_source() -> None:
    runner = package.BLENDER_SCENE_RUNNER
    assert runner.count(package.VIEWER_ORIENTATION_SOURCE) == 1
    compile(runner, "blender_scene_runner.py", "exec")
