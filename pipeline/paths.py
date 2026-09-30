"""Filesystem boundaries shared by DashBite stages."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"


def data_dirs(data_root: Path = DATA_ROOT) -> dict[str, Path]:
    """Return the directories owned by the file-based pipeline contract."""

    return {
        "raw": data_root / "raw",
        "features": data_root / "features",
        "models": data_root / "models",
        "predictions": data_root / "predictions",
        "quality": data_root / "quality",
    }


def ensure_data_dirs(data_root: Path = DATA_ROOT) -> dict[str, Path]:
    """Create and return all pipeline data directories."""

    directories = data_dirs(data_root)
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories
