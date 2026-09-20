import pytest


@pytest.mark.unit
def test_registered_markers_and_fast_default(pytestconfig, repo_root):
    markers = "\n".join(pytestconfig.getini("markers"))
    assert "unit:" in markers
    assert "integration:" in markers
    assert "slow:" in markers
    assert pytestconfig.getoption("markexpr") == "not slow"
    assert (repo_root / "pyproject.toml").is_file()


@pytest.mark.slow
def test_slow_marker_can_be_selected_explicitly():
    assert True
