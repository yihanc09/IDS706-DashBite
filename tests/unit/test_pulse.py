from datetime import datetime, timezone

import pytest

from pipeline.pulse import (
    field_failure_counts,
    late_flag_rate_over_time,
    score_summary,
    sample_volume,
    volume_over_time,
)


NOW = datetime(2026, 9, 23, 14, 5, tzinfo=timezone.utc)


@pytest.mark.unit
def test_sample_volume_and_score_summary():
    assert sample_volume([{"order_id": "a"}, {"order_id": "b"}]) == 2
    assert score_summary(
        [{"predicted_late": "1"}, {"predicted_late": "0"}, {"predicted_late": "1"}]
    ) == {
        "prediction_count": 3,
        "predicted_late_count": 2,
        "late_flag_rate": 2 / 3,
    }


@pytest.mark.unit
def test_volume_over_time_buckets_and_filters_recent_window():
    rows = [
        {"timestamp": "2026-09-23T14:05:42+00:00"},
        {"timestamp": "2026-09-23T14:04:01+00:00"},
        {"timestamp": "2026-09-23T12:00:00+00:00"},
    ]

    series = volume_over_time(rows, now=NOW, window_minutes=2)

    assert series == [
        {"minute": datetime(2026, 9, 23, 14, 4, tzinfo=timezone.utc), "sample_count": 1},
        {"minute": datetime(2026, 9, 23, 14, 5, tzinfo=timezone.utc), "sample_count": 1},
    ]


@pytest.mark.unit
def test_late_flag_rate_joins_order_id_to_feature_timestamp():
    features = [
        {"order_id": "a", "timestamp": "2026-09-23T14:04:10+00:00"},
        {"order_id": "b", "timestamp": "2026-09-23T14:04:20+00:00"},
    ]
    predictions = [
        {"order_id": "a", "predicted_late": "1"},
        {"order_id": "b", "predicted_late": "0"},
        {"order_id": "missing", "predicted_late": "1"},
    ]

    series = late_flag_rate_over_time(features, predictions, now=NOW, window_minutes=2)

    assert series[-2:] == [
        {"minute": datetime(2026, 9, 23, 14, 4, tzinfo=timezone.utc), "flag_rate": 0.5},
        {"minute": datetime(2026, 9, 23, 14, 5, tzinfo=timezone.utc), "flag_rate": 0.0},
    ]


@pytest.mark.unit
def test_field_failures_are_ranked():
    assert field_failure_counts(
        [{"field": "timestamp"}, {"field": "timestamp"}, {"field": "distance_km"}]
    ) == [
        {"field": "timestamp", "failure_count": 2},
        {"field": "distance_km", "failure_count": 1},
    ]
