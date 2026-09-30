import pytest

from pipeline.train import MODEL_FEATURES


@pytest.mark.regression
def test_training_feature_contract_is_stable():
    assert MODEL_FEATURES == ["distance_km", "prep_minutes"]
