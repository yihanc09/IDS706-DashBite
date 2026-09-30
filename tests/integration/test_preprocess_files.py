import csv

import pytest

from pipeline.paths import ensure_data_dirs
from pipeline.preprocess import FEATURE_FIELDNAMES, process_once


@pytest.mark.integration
def test_one_preprocessing_tick_writes_clean_feature_snapshot(tmp_path):
    directories = ensure_data_dirs(tmp_path / "data")
    raw_path = directories["raw"] / "orders.csv"
    with raw_path.open("w", newline="", encoding="utf-8") as raw_file:
        writer = csv.DictWriter(
            raw_file,
            fieldnames=[
                "order_id",
                "timestamp",
                "distance_km",
                "prep_minutes",
                "order_value",
                "was_late",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "order_id": "order-good",
                    "timestamp": "2026-09-23T18:05:00+00:00",
                    "distance_km": "3.2",
                    "prep_minutes": "24",
                    "order_value": "31.00",
                    "was_late": "0",
                },
                {
                    "order_id": "order-bad",
                    "timestamp": "not-a-timestamp",
                    "distance_km": "3.2",
                    "prep_minutes": "24",
                    "order_value": "31.00",
                    "was_late": "0",
                },
            ]
        )

    accepted, rejected = process_once(
        directories["raw"], directories["features"] / "features.csv"
    )

    assert (accepted, rejected) == (1, 1)
    with (directories["features"] / "features.csv").open(
        newline="", encoding="utf-8"
    ) as feature_file:
        rows = list(csv.DictReader(feature_file))
    assert list(rows[0]) == FEATURE_FIELDNAMES
    assert rows[0]["order_id"] == "order-good"
    assert rows[0]["hour"] == "18"
    assert rows[0]["is_peak"] == "1"
    assert rows[0]["was_late"] == "0"
