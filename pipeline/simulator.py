"""Synthetic food-delivery order intake process."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import logging
from pathlib import Path
import random
import signal
import time

from pipeline.config import load_config
from pipeline.paths import ensure_data_dirs


LOGGER = logging.getLogger("dashbite.simulator")
FIELDNAMES = [
    "order_id",
    "timestamp",
    "distance_km",
    "prep_minutes",
    "order_value",
    "was_late",
]


class Simulator:
    """Write synthetic orders to a CSV batch at a configurable cadence."""

    def __init__(
        self,
        output_dir: Path,
        batch_size: int,
        poll_interval_seconds: float,
        rng: random.Random | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds
        self.rng = rng or random.Random()
        self._stopped = False
        self._next_order_id = 1

    def stop(self, _signum: int | None = None, _frame: object | None = None) -> None:
        self._stopped = True

    def run(self) -> None:
        LOGGER.info(
            "Simulator started: writing %d orders every %.1fs to %s",
            self.batch_size,
            self.poll_interval_seconds,
            self.output_dir,
        )
        while not self._stopped:
            output_path = self.write_batch()
            LOGGER.info("Wrote %d synthetic orders to %s", self.batch_size, output_path)
            if self._stopped:
                break
            time.sleep(self.poll_interval_seconds)
        LOGGER.info("Simulator stopped")

    def write_batch(self) -> Path:
        timestamp = datetime.now(timezone.utc).isoformat()
        output_path = self.output_dir / "orders.csv"
        is_new_file = not output_path.exists() or output_path.stat().st_size == 0
        rows = [self._make_order(timestamp) for _ in range(self.batch_size)]
        with output_path.open("a", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
            if is_new_file:
                writer.writeheader()
            writer.writerows(rows)
        return output_path

    def _make_order(self, timestamp: str) -> dict[str, str | float | int]:
        distance = round(self.rng.uniform(0.5, 15.0), 2)
        prep_minutes = self.rng.randint(8, 45)
        order_value = round(self.rng.uniform(10.0, 120.0), 2)
        late_probability = min(0.9, 0.08 + distance / 35 + prep_minutes / 150)
        order_id = f"order-{self._next_order_id:06d}"
        self._next_order_id += 1
        return {
            "order_id": order_id,
            "timestamp": timestamp,
            "distance_km": distance,
            "prep_minutes": prep_minutes,
            "order_value": order_value,
            "was_late": int(self.rng.random() < late_probability),
        }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config()
    directories = ensure_data_dirs()
    simulator = Simulator(
        output_dir=directories["raw"],
        batch_size=config.batch_size,
        poll_interval_seconds=config.poll_interval_seconds,
    )
    signal.signal(signal.SIGINT, simulator.stop)
    signal.signal(signal.SIGTERM, simulator.stop)
    simulator.run()


if __name__ == "__main__":
    main()
