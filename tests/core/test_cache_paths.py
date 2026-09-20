import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "core" / "src" / "packlab_core" / "cache_paths.py"
SPEC = importlib.util.spec_from_file_location("cache_paths", MODULE_PATH)
assert SPEC and SPEC.loader
cache_paths = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache_paths)


def test_platform_defaults_are_deterministic(tmp_path):
    env = {"LOCALAPPDATA": str(tmp_path / "local"), "XDG_CACHE_HOME": str(tmp_path / "xdg-cache"), "XDG_DATA_HOME": str(tmp_path / "xdg-data")}
    assert cache_paths.cache_root(env=env, home=tmp_path / "home", system="Windows") == tmp_path / "local" / "PackLab"
    assert cache_paths.cache_root(env=env, home=tmp_path / "home", system="Darwin") == tmp_path / "home" / "Library" / "Caches" / "PackLab"
    assert cache_paths.cache_root(env=env, home=tmp_path / "home", system="Linux") == tmp_path / "xdg-cache" / "packlab"


def test_overrides_and_lazy_creation_use_only_temp_paths(tmp_path):
    env = {"PACKLAB_CACHE_ROOT": str(tmp_path / "cache"), "PACKLAB_DATA_ROOT": str(tmp_path / "data")}
    roots = cache_paths.ensure_directories(env=env, home=tmp_path / "unused", system="Windows")
    assert roots["cache"] == tmp_path / "cache"
    assert roots["workspace"] == tmp_path / "cache" / "work"
    assert roots["project_data"] == tmp_path / "data"
    assert all(path.is_dir() for path in roots.values())


def test_workspace_and_project_data_are_distinct(tmp_path):
    env = {"PACKLAB_CACHE_ROOT": str(tmp_path / "cache")}
    assert cache_paths.workspace_root(env=env, home=tmp_path, system="Linux") != cache_paths.project_data_root(env=env, home=tmp_path, system="Linux")
