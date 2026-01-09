"""Shared pytest fixtures for podcast automation tests."""

import pathlib
import pytest


@pytest.fixture
def samples_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Provide a temporary directory for staging sample media files."""
    return tmp_path
