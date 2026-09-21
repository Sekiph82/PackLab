import subprocess
import sys

import pytest


@pytest.mark.unit
def test_registered_markers_and_fast_default(pytestconfig, repo_root):
    markers = "\n".join(pytestconfig.getini("markers"))
    assert "unit:" in markers
    assert "integration:" in markers
    assert "slow:" in markers
    assert pytestconfig.getoption("markexpr") == "not slow"
    assert pytestconfig.getoption("strict_markers") is True
    assert (repo_root / "pyproject.toml").is_file()


def test_unknown_marker_fails_collection(tmp_path, repo_root):
    unknown_test = tmp_path / "test_unknown_marker.py"
    unknown_test.write_text(
        "import pytest\n"
        "@pytest.mark.intentionally_unknown\n"
        "def test_should_not_collect():\n"
        "    pass\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(repo_root / "pyproject.toml"),
            "-q",
            str(unknown_test),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "intentionally_unknown" in completed.stdout + completed.stderr


@pytest.mark.slow
def test_slow_marker_can_be_selected_explicitly():
    assert True
