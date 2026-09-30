import csv
import random

import pytest

from pipeline.simulator import FIELDNAMES, Simulator


@pytest.mark.unit
def test_write_batch_creates_expected_order_rows(tmp_path):
    simulator = Simulator(tmp_path, batch_size=2, poll_interval_seconds=1, rng=random.Random(7))

    output_path = simulator.write_batch()

    with output_path.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))
    assert output_path.name == "orders.csv"
    assert len(rows) == 2
    assert list(rows[0]) == FIELDNAMES
    assert rows[0]["order_id"] == "order-000001"
    assert rows[0]["was_late"] in {"0", "1"}


@pytest.mark.unit
def test_stop_prevents_another_batch(tmp_path):
    simulator = Simulator(tmp_path, batch_size=1, poll_interval_seconds=1)
    simulator.stop()
    simulator.run()

    assert not (tmp_path / "orders.csv").exists()
