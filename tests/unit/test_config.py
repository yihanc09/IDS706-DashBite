import pytest

from pipeline.config import load_config


@pytest.mark.unit
def test_defaults(monkeypatch):
    for name in ("TRAIN_EVERY_N_EVENTS", "BATCH_SIZE", "POLL_INTERVAL_SECONDS"):
        monkeypatch.delenv(name, raising=False)

    config = load_config()

    assert config.train_every_n_events == 2000
    assert config.batch_size == 50
    assert config.poll_interval_seconds == 15.0


@pytest.mark.unit
def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("TRAIN_EVERY_N_EVENTS", "10")
    monkeypatch.setenv("BATCH_SIZE", "3")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "0.25")

    config = load_config()

    assert config.train_every_n_events == 10
    assert config.batch_size == 3
    assert config.poll_interval_seconds == 0.25
