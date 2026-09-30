import json

import pytest

from pipeline.train import MODEL_FEATURES, train_once


def _write_features(path, rows):
    path.write_text(
        "order_id,timestamp,distance_km,prep_minutes,order_value,hour,is_peak,was_late\n"
        + "\n".join(
            f"{order_id},2026-09-23T12:00:00+00:00,{distance},{prep},20,12,1,{label}"
            for order_id, distance, prep, label in rows
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.unit
def test_training_honors_threshold_and_publishes_metrics(tmp_path):
    feature_path = tmp_path / "features.csv"
    model_dir = tmp_path / "models"
    _write_features(
        feature_path,
        [(f"order-{index}", index + 1, index + 10, index % 2) for index in range(4)],
    )

    skipped = train_once(feature_path, model_dir, train_every_n_events=5)
    published = train_once(feature_path, model_dir, train_every_n_events=4)

    assert not skipped.published
    assert published.published
    assert json.loads(published.metrics_path.read_text())["feature_names"] == MODEL_FEATURES
