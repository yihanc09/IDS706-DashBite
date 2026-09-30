import pytest

from pipeline.simulator import FIELDNAMES


@pytest.mark.regression
def test_raw_order_schema_is_stable():
    assert FIELDNAMES == [
        "order_id",
        "timestamp",
        "distance_km",
        "prep_minutes",
        "order_value",
        "was_late",
    ]
