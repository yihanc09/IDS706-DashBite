import pytest

from pipeline.preprocess import FEATURE_FIELDNAMES


@pytest.mark.regression
def test_feature_schema_is_stable():
    assert FEATURE_FIELDNAMES == [
        "order_id",
        "timestamp",
        "distance_km",
        "prep_minutes",
        "order_value",
        "hour",
        "is_peak",
        "was_late",
    ]
