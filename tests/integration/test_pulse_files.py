import csv

import pytest

from pipeline.pulse import (
    field_failure_counts,
    late_flag_rate_over_time,
    read_csv,
    volume_over_time,
)


@pytest.mark.integration
def test_pulse_helpers_read_artifacts_without_mutating_them(tmp_path):
    features_path = tmp_path / "features.csv"
    predictions_path = tmp_path / "predictions.csv"
    quality_path = tmp_path / "quality.csv"
    features_path.write_text(
        "order_id,timestamp\norder-1,2026-09-23T14:05:00+00:00\n",
        encoding="utf-8",
    )
    predictions_path.write_text(
        "order_id,predicted_late\norder-1,1\n",
        encoding="utf-8",
    )
    quality_path.write_text("field\n timestamp\n", encoding="utf-8")

    feature_rows = read_csv(features_path)
    prediction_rows = read_csv(predictions_path)
    quality_rows = read_csv(quality_path)
    assert volume_over_time(
        feature_rows, now=__import__("datetime").datetime.fromisoformat("2026-09-23T14:05:00+00:00"), window_minutes=1
    )[-1]["sample_count"] == 1
    assert late_flag_rate_over_time(
        feature_rows, prediction_rows, now=__import__("datetime").datetime.fromisoformat("2026-09-23T14:05:00+00:00"), window_minutes=1
    )[-1]["flag_rate"] == 1.0
    assert field_failure_counts(quality_rows) == [{"field": "timestamp", "failure_count": 1}]
    assert features_path.exists() and predictions_path.exists() and quality_path.exists()
