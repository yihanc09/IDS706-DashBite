import pytest

from pipeline.infer import MODEL_FEATURES, PREDICTION_FIELDNAMES


@pytest.mark.regression
def test_prediction_schema_is_stable():
    assert PREDICTION_FIELDNAMES == [
        "order_id",
        "late_probability",
        "predicted_late",
        "checkpoint_id",
    ]


@pytest.mark.regression
def test_inference_model_interface_is_stable():
    assert MODEL_FEATURES == ["distance_km", "prep_minutes"]
