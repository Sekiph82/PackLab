from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the checkout root without depending on the caller's cwd."""

    return Path(__file__).resolve().parents[1]
