"""Shared environment-driven configuration for DashBite."""

from dataclasses import dataclass
import os


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero, got {parsed}")
    return parsed


@dataclass(frozen=True)
class Config:
    """Runtime settings shared by pipeline stages."""

    train_every_n_events: int = 2000
    batch_size: int = 50
    poll_interval_seconds: float = 15.0


def load_config() -> Config:
    """Load configuration, applying supported environment overrides."""

    poll_value = os.getenv("POLL_INTERVAL_SECONDS")
    try:
        poll_interval = (
            Config.poll_interval_seconds if poll_value is None else float(poll_value)
        )
    except ValueError as exc:
        raise ValueError(
            f"POLL_INTERVAL_SECONDS must be a number, got {poll_value!r}"
        ) from exc
    if poll_interval <= 0:
        raise ValueError(
            f"POLL_INTERVAL_SECONDS must be greater than zero, got {poll_interval}"
        )

    return Config(
        train_every_n_events=_positive_int("TRAIN_EVERY_N_EVENTS", 2000),
        batch_size=_positive_int("BATCH_SIZE", 50),
        poll_interval_seconds=poll_interval,
    )
