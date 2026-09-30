import csv
import json

import joblib
import pytest
from sklearn.linear_model import LogisticRegression

from pipeline.infer import infer_once


@pytest.mark.integration
def test_inference_scores_new_features_from_existing_checkpoint(tmp_path):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    model = LogisticRegression().fit([[1, 1], [2, 2], [3, 3], [4, 4]], [0, 0, 1, 1])
    joblib.dump(
        {"model": model, "feature_names": ["distance_km", "prep_minutes"], "version": 1},
        model_dir / "model-v001.joblib",
    )
    (model_dir / "model-v001.metrics.json").write_text(
        json.dumps({"version": 1, "sample_count": 4}),
        encoding="utf-8",
    )
    feature_path = tmp_path / "features.csv"
    feature_path.write_text(
        "order_id,distance_km,prep_minutes\norder-1,4,4\n",
        encoding="utf-8",
    )
    prediction_path = tmp_path / "predictions" / "predictions.csv"

    assert infer_once(feature_path, model_dir, prediction_path) == 1
    with prediction_path.open(newline="", encoding="utf-8") as prediction_file:
        row = next(csv.DictReader(prediction_file))
    assert row["order_id"] == "order-1"
    assert row["checkpoint_id"] == "model-v001"

    feature_path.write_text(
        "order_id,distance_km,prep_minutes\norder-2,1,1\n",
        encoding="utf-8",
    )
    assert infer_once(feature_path, model_dir, prediction_path) == 1
    with prediction_path.open(newline="", encoding="utf-8") as prediction_file:
        updated_row = next(csv.DictReader(prediction_file))
    assert updated_row["order_id"] == "order-2"
    assert updated_row["checkpoint_id"] == "model-v001"
