"""Score feature rows using the newest published model checkpoint."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
import pickle
import re
import signal
import time

import joblib

from pipeline.config import load_config
from pipeline.paths import ensure_data_dirs


LOGGER = logging.getLogger("dashbite.infer")
MODEL_FEATURES = ["distance_km", "prep_minutes"]
MODEL_PATTERN = re.compile(r"^model-v(\d{3})\.joblib$")
PREDICTION_FIELDNAMES = [
    "order_id",
    "late_probability",
    "predicted_late",
    "checkpoint_id",
]
DECISION_THRESHOLD = 0.5


def find_newest_checkpoint(model_dir: Path) -> tuple[Path, str] | None:
    """Return the newest valid model/metrics pair, ignoring partial artifacts."""

    candidates: list[tuple[int, Path, str]] = []
    if not model_dir.exists():
        return None
    for model_path in model_dir.iterdir():
        match = MODEL_PATTERN.match(model_path.name)
        if not match:
            continue
        version = int(match.group(1))
        checkpoint_id = f"model-v{version:03d}"
        metrics_path = model_dir / f"{checkpoint_id}.metrics.json"
        try:
            with metrics_path.open(encoding="utf-8") as metrics_file:
                metrics = json.load(metrics_file)
            if metrics.get("version") != version:
                continue
            payload = joblib.load(model_path)
            if payload.get("feature_names") != MODEL_FEATURES:
                continue
            if not hasattr(payload.get("model"), "predict_proba"):
                continue
        except (
            OSError,
            EOFError,
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
            json.JSONDecodeError,
            pickle.UnpicklingError,
        ):
            continue
        candidates.append((version, model_path, checkpoint_id))
    if not candidates:
        return None
    _, model_path, checkpoint_id = max(candidates, key=lambda candidate: candidate[0])
    return model_path, checkpoint_id


def infer_once(
    feature_path: Path,
    model_dir: Path,
    prediction_path: Path,
) -> int | None:
    """Score the current feature snapshot once, returning rows written."""

    checkpoint = find_newest_checkpoint(model_dir)
    if checkpoint is None:
        return None
    model_path, checkpoint_id = checkpoint
    try:
        payload = joblib.load(model_path)
    except (OSError, EOFError, pickle.UnpicklingError):
        return None
    model = payload["model"]
    with feature_path.open(newline="", encoding="utf-8") as feature_file:
        reader = csv.DictReader(feature_file)
        required = {"order_id", *MODEL_FEATURES}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{feature_path} is missing required inference columns")
        rows = []
        feature_values = []
        for row in reader:
            try:
                feature_values.append([float(row[name]) for name in MODEL_FEATURES])
                rows.append(row)
            except (TypeError, ValueError):
                continue

    if rows:
        probability_matrix = model.predict_proba(feature_values)
        class_index = list(model.classes_).index(1)
        probabilities = probability_matrix[:, class_index]
    else:
        probabilities = []
    prediction_rows = [
        {
            "order_id": row["order_id"],
            "late_probability": round(float(probability), 6),
            "predicted_late": int(probability >= DECISION_THRESHOLD),
            "checkpoint_id": checkpoint_id,
        }
        for row, probability in zip(rows, probabilities)
    ]
    prediction_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = prediction_path.with_suffix(".tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=PREDICTION_FIELDNAMES)
        writer.writeheader()
        writer.writerows(prediction_rows)
    temporary_path.replace(prediction_path)
    return len(prediction_rows)


class Inference:
    """Poll for a checkpoint and feature snapshot, then refresh predictions."""

    def __init__(
        self,
        feature_path: Path,
        model_dir: Path,
        prediction_path: Path,
        poll_interval_seconds: float,
    ) -> None:
        self.feature_path = feature_path
        self.model_dir = model_dir
        self.prediction_path = prediction_path
        self.poll_interval_seconds = poll_interval_seconds
        self._stopped = False

    def stop(self, _signum: int | None = None, _frame: object | None = None) -> None:
        self._stopped = True

    def run(self) -> None:
        LOGGER.info("Inference started")
        while not self._stopped:
            if not self.feature_path.exists():
                LOGGER.info("Waiting for feature file: %s", self.feature_path)
            else:
                checkpoint = find_newest_checkpoint(self.model_dir)
                if checkpoint is None:
                    LOGGER.info("Waiting for a complete model checkpoint in %s", self.model_dir)
                else:
                    rows_written = infer_once(
                        self.feature_path,
                        self.model_dir,
                        self.prediction_path,
                    )
                    LOGGER.info(
                        "Scored %d rows with %s into %s",
                        rows_written,
                        checkpoint[1],
                        self.prediction_path,
                    )
            if not self._stopped:
                time.sleep(self.poll_interval_seconds)
        LOGGER.info("Inference stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()
    directories = ensure_data_dirs()
    inference = Inference(
        feature_path=directories["features"] / "features.csv",
        model_dir=directories["models"],
        prediction_path=directories["predictions"] / "predictions.csv",
        poll_interval_seconds=config.poll_interval_seconds,
    )
    signal.signal(signal.SIGINT, inference.stop)
    signal.signal(signal.SIGTERM, inference.stop)
    inference.run()


if __name__ == "__main__":
    main()
