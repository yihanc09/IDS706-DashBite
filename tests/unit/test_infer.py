import json

import joblib
import pytest
from sklearn.linear_model import LogisticRegression

from pipeline.infer import DECISION_THRESHOLD, find_newest_checkpoint, infer_once


def _write_checkpoint(model_dir, version, sample_count=4):
    model_dir.mkdir(parents=True, exist_ok=True)
    model = LogisticRegression().fit([[1, 1], [2, 2], [3, 3], [4, 4]], [0, 0, 1, 1])
    joblib.dump(
        {"model": model, "feature_names": ["distance_km", "prep_minutes"], "version": version},
        model_dir / f"model-v{version:03d}.joblib",
    )
    (model_dir / f"model-v{version:03d}.metrics.json").write_text(
        json.dumps({"version": version, "sample_count": sample_count}),
        encoding="utf-8",
    )


@pytest.mark.unit
def test_newest_complete_checkpoint_ignores_partial_version(tmp_path):
    _write_checkpoint(tmp_path, 1)
    (tmp_path / "model-v002.joblib").write_bytes(b"partial")

    assert find_newest_checkpoint(tmp_path)[1] == "model-v001"


@pytest.mark.unit
def test_newest_checkpoint_ignores_malformed_payload(tmp_path):
    _write_checkpoint(tmp_path, 1)
    joblib.dump(["not", "a", "checkpoint"], tmp_path / "model-v002.joblib")
    (tmp_path / "model-v002.metrics.json").write_text(
        json.dumps({"version": 2, "sample_count": 4}),
        encoding="utf-8",
    )

    assert find_newest_checkpoint(tmp_path)[1] == "model-v001"


@pytest.mark.unit
def test_infer_once_writes_predictions_with_checkpoint_id(tmp_path):
    model_dir = tmp_path / "models"
    _write_checkpoint(model_dir, 3)
    feature_path = tmp_path / "features.csv"
    feature_path.write_text(
        "order_id,distance_km,prep_minutes\norder-1,4,4\norder-2,1,1\n",
        encoding="utf-8",
    )

    assert infer_once(feature_path, model_dir, tmp_path / "predictions.csv") == 2
    lines = (tmp_path / "predictions.csv").read_text().splitlines()
    assert lines[0] == "order_id,late_probability,predicted_late,checkpoint_id"
    assert all(line.endswith(",model-v003") for line in lines[1:])


@pytest.mark.unit
def test_infer_once_waits_without_checkpoint(tmp_path):
    feature_path = tmp_path / "features.csv"
    feature_path.write_text("order_id,distance_km,prep_minutes\n", encoding="utf-8")

    assert infer_once(feature_path, tmp_path / "models", tmp_path / "predictions.csv") is None
    assert not (tmp_path / "predictions.csv").exists()


@pytest.mark.unit
def test_decision_threshold_is_explicit():
    assert DECISION_THRESHOLD == 0.5
