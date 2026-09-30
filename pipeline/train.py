"""Train and publish versioned late-order models."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
import signal
import time

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from pipeline.config import load_config
from pipeline.paths import ensure_data_dirs


LOGGER = logging.getLogger("dashbite.train")
MODEL_FEATURES = ["distance_km", "prep_minutes"]
MODEL_PATTERN = re.compile(r"^model-v(\d{3})\.joblib$")


@dataclass(frozen=True)
class TrainingResult:
    published: bool
    version: int | None
    sample_count: int
    new_sample_count: int
    model_path: Path | None = None
    metrics_path: Path | None = None


def _read_labeled_rows(feature_path: Path) -> list[tuple[list[float], int]]:
    with feature_path.open(newline="", encoding="utf-8") as feature_file:
        reader = csv.DictReader(feature_file)
        required = set(MODEL_FEATURES + ["was_late"])
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{feature_path} is missing required training columns")

        rows = []
        for row in reader:
            try:
                features = [float(row[name]) for name in MODEL_FEATURES]
                label = int(row["was_late"])
            except (TypeError, ValueError):
                continue
            if label not in (0, 1):
                continue
            rows.append((features, label))
        return rows


def _latest_version(model_dir: Path) -> int:
    versions = []
    for path in model_dir.iterdir():
        match = MODEL_PATTERN.match(path.name)
        if not match:
            continue
        version = int(match.group(1))
        if _latest_sample_count(model_dir, version) is not None:
            versions.append(version)
    return max(versions, default=0)


def train_once(
    feature_path: Path,
    model_dir: Path,
    train_every_n_events: int,
) -> TrainingResult:
    """Publish a model when enough new labeled rows are available."""

    if train_every_n_events <= 0:
        raise ValueError("train_every_n_events must be greater than zero")
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature file not found: {feature_path}")

    rows = _read_labeled_rows(feature_path)
    latest_version = _latest_version(model_dir) if model_dir.exists() else 0
    latest_sample_count = _latest_sample_count(model_dir, latest_version)
    new_sample_count = max(0, len(rows) - latest_sample_count)
    if new_sample_count < train_every_n_events:
        return TrainingResult(
            published=False,
            version=None,
            sample_count=len(rows),
            new_sample_count=new_sample_count,
        )
    if len({label for _, label in rows}) < 2:
        raise ValueError("training requires both on-time and late labels")

    model = LogisticRegression(random_state=0, max_iter=1000)
    x_values = [features for features, _ in rows]
    y_values = [label for _, label in rows]
    model.fit(x_values, y_values)
    predictions = model.predict(x_values)
    version = latest_version + 1
    model_path = model_dir / f"model-v{version:03d}.joblib"
    metrics_path = model_dir / f"model-v{version:03d}.metrics.json"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_payload = {
        "model": model,
        "feature_names": MODEL_FEATURES,
        "version": version,
        "sample_count": len(rows),
    }
    _atomic_joblib_dump(model_payload, model_path)
    metrics = {
        "version": version,
        "sample_count": len(rows),
        "new_sample_count": new_sample_count,
        "feature_names": MODEL_FEATURES,
        "accuracy": accuracy_score(y_values, predictions),
    }
    _atomic_json_dump(metrics, metrics_path)
    return TrainingResult(
        published=True,
        version=version,
        sample_count=len(rows),
        new_sample_count=new_sample_count,
        model_path=model_path,
        metrics_path=metrics_path,
    )


def _latest_sample_count(model_dir: Path, version: int) -> int | None:
    if version == 0:
        return 0
    metrics_path = model_dir / f"model-v{version:03d}.metrics.json"
    try:
        with metrics_path.open(encoding="utf-8") as metrics_file:
            sample_count = int(json.load(metrics_file)["sample_count"])
        if sample_count < 0:
            return None
        return sample_count
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _atomic_joblib_dump(payload: object, path: Path) -> None:
    temporary_path = path.with_suffix(".tmp")
    joblib.dump(payload, temporary_path)
    temporary_path.replace(path)


def _atomic_json_dump(payload: dict[str, object], path: Path) -> None:
    temporary_path = path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as metrics_file:
        json.dump(payload, metrics_file, indent=2, sort_keys=True)
        metrics_file.write("\n")
    temporary_path.replace(path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop",
        action="store_true",
        help="keep polling for new labeled examples after each training attempt",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()
    directories = ensure_data_dirs()
    feature_path = directories["features"] / "features.csv"
    model_dir = directories["models"]
    stopped = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    while not stopped:
        try:
            result = train_once(
                feature_path=feature_path,
                model_dir=model_dir,
                train_every_n_events=config.train_every_n_events,
            )
            if result.published:
                LOGGER.info(
                    "Published model v%03d and metrics sidecar for %d samples",
                    result.version,
                    result.sample_count,
                )
            else:
                LOGGER.info(
                    "Training skipped: %d new labeled samples, %d required",
                    result.new_sample_count,
                    config.train_every_n_events,
                )
        except FileNotFoundError:
            LOGGER.info("Waiting for feature file: %s", feature_path)
        if not args.loop:
            break
        if not stopped:
            time.sleep(config.poll_interval_seconds)
    LOGGER.info("Training stopped")


if __name__ == "__main__":
    main()
