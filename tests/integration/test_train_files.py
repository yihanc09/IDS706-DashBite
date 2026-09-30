import csv
import json

import joblib
import pytest

import pipeline.train as train_module
from pipeline.train import train_once


@pytest.mark.integration
def test_training_publishes_versioned_checkpoint_and_increments(tmp_path):
    feature_path = tmp_path / "features.csv"
    model_dir = tmp_path / "models"
    with feature_path.open("w", newline="", encoding="utf-8") as feature_file:
        writer = csv.DictWriter(
            feature_file,
            fieldnames=[
                "order_id",
                "timestamp",
                "distance_km",
                "prep_minutes",
                "order_value",
                "hour",
                "is_peak",
                "was_late",
            ],
        )
        writer.writeheader()
        for index in range(6):
            writer.writerow(
                {
                    "order_id": f"order-{index}",
                    "timestamp": "2026-09-23T12:00:00+00:00",
                    "distance_km": index + 1,
                    "prep_minutes": index + 8,
                    "order_value": 20,
                    "hour": 12,
                    "is_peak": 1,
                    "was_late": index % 2,
                }
            )

    first = train_once(feature_path, model_dir, train_every_n_events=6)
    with feature_path.open("a", encoding="utf-8") as feature_file:
        for index in range(6, 12):
            feature_file.write(
                f"order-{index},2026-09-23T12:00:00+00:00,{index + 1},{index + 8},"
                f"20,12,1,{index % 2}\n"
            )
    second = train_once(feature_path, model_dir, train_every_n_events=6)

    assert first.model_path.name == "model-v001.joblib"
    assert first.metrics_path.name == "model-v001.metrics.json"
    assert second.published is True
    assert second.model_path.name == "model-v002.joblib"
    assert second.new_sample_count == 6
    assert joblib.load(first.model_path)["feature_names"] == ["distance_km", "prep_minutes"]
    metrics = json.loads(first.metrics_path.read_text())
    assert metrics["sample_count"] == 6
    assert sorted(path.name for path in model_dir.iterdir()) == [
        "model-v001.joblib",
        "model-v001.metrics.json",
        "model-v002.joblib",
        "model-v002.metrics.json",
    ]


@pytest.mark.integration
def test_incomplete_publication_does_not_advance_training_version(tmp_path, monkeypatch):
    feature_path = tmp_path / "features.csv"
    model_dir = tmp_path / "models"
    feature_path.write_text(
        "order_id,timestamp,distance_km,prep_minutes,order_value,hour,is_peak,was_late\n"
        + "\n".join(
            f"order-{index},2026-09-23T12:00:00+00:00,{index + 1},{index + 8},20,12,1,{index % 2}"
            for index in range(4)
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_metrics_dump(_payload, _path):
        raise OSError("simulated sidecar failure")

    monkeypatch.setattr(train_module, "_atomic_json_dump", fail_metrics_dump)
    with pytest.raises(OSError, match="simulated sidecar failure"):
        train_once(feature_path, model_dir, train_every_n_events=4)

    monkeypatch.undo()
    result = train_once(feature_path, model_dir, train_every_n_events=4)

    assert result.version == 1
    assert result.new_sample_count == 4
    assert (model_dir / "model-v001.metrics.json").exists()
    assert not (model_dir / "model-v002.joblib").exists()
