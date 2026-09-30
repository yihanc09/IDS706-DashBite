import pytest

from pipeline.paths import ensure_data_dirs


@pytest.mark.unit
def test_ensure_data_dirs_creates_expected_directories(tmp_path):
    directories = ensure_data_dirs(tmp_path / "data")

    assert set(directories) == {"raw", "features", "models", "predictions", "quality"}
    assert all(directory.is_dir() for directory in directories.values())
    assert ensure_data_dirs(tmp_path / "data") == directories
