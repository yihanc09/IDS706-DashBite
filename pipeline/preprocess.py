"""Convert raw order CSVs into clean feature snapshots."""

from __future__ import annotations

import csv
from datetime import datetime
import logging
import math
from pathlib import Path
import signal
import time

from pipeline.config import load_config
from pipeline.paths import ensure_data_dirs


LOGGER = logging.getLogger("dashbite.preprocess")
RAW_FIELDNAMES = [
    "order_id",
    "timestamp",
    "distance_km",
    "prep_minutes",
    "order_value",
    "was_late",
]
FEATURE_FIELDNAMES = [
    "order_id",
    "timestamp",
    "distance_km",
    "prep_minutes",
    "order_value",
    "hour",
    "is_peak",
    "was_late",
]
PEAK_HOURS = set(range(11, 15)) | set(range(17, 21))


def preprocess_file(raw_path: Path, feature_path: Path) -> tuple[int, int]:
    """Clean one raw CSV and write a deterministic feature snapshot."""

    accepted: list[dict[str, str | int | float]] = []
    rejected = 0
    with raw_path.open(newline="", encoding="utf-8") as raw_file:
        reader = csv.DictReader(raw_file)
        if reader.fieldnames != RAW_FIELDNAMES:
            raise ValueError(
                f"{raw_path} has unexpected columns: {reader.fieldnames!r}"
            )
        for row in reader:
            try:
                accepted.append(_feature_row(row))
            except (KeyError, TypeError, ValueError):
                rejected += 1

    feature_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = feature_path.with_suffix(".tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as feature_file:
        writer = csv.DictWriter(feature_file, fieldnames=FEATURE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(accepted)
    temporary_path.replace(feature_path)
    return len(accepted), rejected


def _feature_row(row: dict[str, str | None]) -> dict[str, str | int | float]:
    order_id = (row.get("order_id") or "").strip()
    timestamp = (row.get("timestamp") or "").strip()
    if not order_id or not timestamp:
        raise ValueError("order_id and timestamp are required")

    parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    distance_km = float(row["distance_km"] or "")
    prep_minutes = int(row["prep_minutes"] or "")
    order_value = float(row["order_value"] or "")
    was_late = int(row["was_late"] or "")
    if (
        not math.isfinite(distance_km)
        or not math.isfinite(order_value)
        or distance_km <= 0
        or prep_minutes <= 0
        or order_value <= 0
        or was_late not in (0, 1)
    ):
        raise ValueError("row contains an invalid value")

    hour = parsed_timestamp.hour
    return {
        "order_id": order_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "prep_minutes": prep_minutes,
        "order_value": order_value,
        "hour": hour,
        "is_peak": int(hour in PEAK_HOURS),
        "was_late": was_late,
    }


def process_once(raw_dir: Path, feature_path: Path) -> tuple[int, int]:
    """Process the canonical raw order file once."""

    raw_path = raw_dir / "orders.csv"
    if not raw_path.exists():
        feature_path.parent.mkdir(parents=True, exist_ok=True)
        with feature_path.open("w", newline="", encoding="utf-8") as feature_file:
            csv.DictWriter(feature_file, fieldnames=FEATURE_FIELDNAMES).writeheader()
        return 0, 0
    return preprocess_file(raw_path, feature_path)


class Preprocessor:
    """Poll raw intake output and refresh the feature snapshot."""

    def __init__(self, raw_dir: Path, feature_path: Path, poll_interval_seconds: float):
        self.raw_dir = raw_dir
        self.feature_path = feature_path
        self.poll_interval_seconds = poll_interval_seconds
        self._stopped = False

    def stop(self, _signum: int | None = None, _frame: object | None = None) -> None:
        self._stopped = True

    def run(self) -> None:
        LOGGER.info(
            "Preprocessor started: reading %s and writing %s",
            self.raw_dir,
            self.feature_path,
        )
        while not self._stopped:
            accepted, rejected = process_once(self.raw_dir, self.feature_path)
            LOGGER.info("Processed rows: accepted=%d rejected=%d", accepted, rejected)
            if not self._stopped:
                time.sleep(self.poll_interval_seconds)
        LOGGER.info("Preprocessor stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()
    directories = ensure_data_dirs()
    preprocessor = Preprocessor(
        raw_dir=directories["raw"],
        feature_path=directories["features"] / "features.csv",
        poll_interval_seconds=config.poll_interval_seconds,
    )
    signal.signal(signal.SIGINT, preprocessor.stop)
    signal.signal(signal.SIGTERM, preprocessor.stop)
    preprocessor.run()


if __name__ == "__main__":
    main()
