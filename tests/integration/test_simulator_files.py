import csv
import random

import pytest

from pipeline.paths import ensure_data_dirs
from pipeline.simulator import Simulator


@pytest.mark.integration
def test_simulator_writes_raw_orders_to_data_boundary(tmp_path):
    directories = ensure_data_dirs(tmp_path / "data")
    simulator = Simulator(
        directories["raw"],
        batch_size=3,
        poll_interval_seconds=1,
        rng=random.Random(1),
    )

    output_path = simulator.write_batch()

    with output_path.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))
    assert output_path.parent == directories["raw"]
    assert len(rows) == 3


@pytest.mark.integration
def test_simulator_advances_order_ids_across_writes(tmp_path):
    directories = ensure_data_dirs(tmp_path / "data")
    simulator = Simulator(
        directories["raw"],
        batch_size=2,
        poll_interval_seconds=1,
        rng=random.Random(1),
    )

    output_path = simulator.write_batch()
    simulator.write_batch()

    with output_path.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))
    order_ids = [row["order_id"] for row in rows]
    assert order_ids == ["order-000001", "order-000002", "order-000003", "order-000004"]
    assert len(order_ids) == len(set(order_ids))
