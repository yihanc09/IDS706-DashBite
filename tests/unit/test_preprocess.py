import pytest

from pipeline.preprocess import _feature_row


@pytest.mark.unit
def test_feature_row_derives_lunch_hour_and_preserves_label():
    row = _feature_row(
        {
            "order_id": "order-1",
            "timestamp": "2026-09-23T12:30:00+00:00",
            "distance_km": "4.5",
            "prep_minutes": "20",
            "order_value": "25.50",
            "was_late": "1",
        }
    )

    assert row == {
        "order_id": "order-1",
        "timestamp": "2026-09-23T12:30:00+00:00",
        "distance_km": 4.5,
        "prep_minutes": 20,
        "order_value": 25.5,
        "hour": 12,
        "is_peak": 1,
        "was_late": 1,
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "field,value",
    [
        ("distance_km", "0"),
        ("prep_minutes", "-1"),
        ("order_value", "0"),
        ("was_late", "2"),
        ("timestamp", "not-a-timestamp"),
    ],
)
def test_feature_row_rejects_invalid_values(field, value):
    row = {
        "order_id": "order-1",
        "timestamp": "2026-09-23T12:30:00+00:00",
        "distance_km": "4.5",
        "prep_minutes": "20",
        "order_value": "25.50",
        "was_late": "1",
    }
    row[field] = value

    with pytest.raises((TypeError, ValueError)):
        _feature_row(row)
