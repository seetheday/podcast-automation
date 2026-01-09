"""Placeholder ingest tests to illustrate structure."""

from pathlib import Path


def test_samples_dir_fixture(samples_dir: Path) -> None:
    """Ensure the shared fixture yields an empty directory."""
    assert samples_dir.exists()
    assert not any(samples_dir.iterdir())
