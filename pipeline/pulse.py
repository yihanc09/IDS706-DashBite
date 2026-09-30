"""Pure data helpers for the read-only Model Pulse dashboard."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping

import csv


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV artifact, returning an empty list when it is not available."""

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def sample_volume(features: Iterable[Mapping[str, str]]) -> int:
    """Count feature samples."""

    return sum(1 for _ in features)


def volume_over_time(
    features: Iterable[Mapping[str, str]],
    *,
    now: datetime | None = None,
    window_minutes: int = 60,
) -> list[dict[str, object]]:
    """Count samples in one-minute UTC buckets over the recent window."""

    cutoff, end = _window(now, window_minutes)
    buckets: Counter[datetime] = Counter()
    for row in features:
        timestamp = _parse_timestamp(row.get("timestamp", ""))
        if timestamp is None:
            continue
        bucket = timestamp.replace(second=0, microsecond=0)
        if cutoff <= bucket <= end:
            buckets[bucket] += 1
    return [
        {"minute": minute, "sample_count": buckets[minute]}
        for minute in _minutes(cutoff, end)
    ]


def score_summary(predictions: Iterable[Mapping[str, str]]) -> dict[str, float | int]:
    """Summarize prediction volume and late-flag rate."""

    rows = list(predictions)
    flagged = sum(_as_binary(row.get("predicted_late")) for row in rows)
    return {
        "prediction_count": len(rows),
        "predicted_late_count": flagged,
        "late_flag_rate": (flagged / len(rows) if rows else 0.0),
    }


def late_flag_rate_over_time(
    features: Iterable[Mapping[str, str]],
    predictions: Iterable[Mapping[str, str]],
    *,
    now: datetime | None = None,
    window_minutes: int = 60,
) -> list[dict[str, object]]:
    """Join predictions to feature timestamps and calculate flag rate per minute."""

    timestamps = {
        row.get("order_id", ""): _parse_timestamp(row.get("timestamp", ""))
        for row in features
    }
    cutoff, end = _window(now, window_minutes)
    totals: Counter[datetime] = Counter()
    flagged: Counter[datetime] = Counter()
    for row in predictions:
        timestamp = timestamps.get(row.get("order_id", ""))
        if timestamp is None:
            continue
        bucket = timestamp.replace(second=0, microsecond=0)
        if cutoff <= bucket <= end:
            totals[bucket] += 1
            flagged[bucket] += _as_binary(row.get("predicted_late"))
    return [
        {
            "minute": minute,
            "flag_rate": (flagged[minute] / totals[minute] if totals[minute] else 0.0),
        }
        for minute in _minutes(cutoff, end)
    ]


def field_failure_counts(
    failures: Iterable[Mapping[str, str]],
) -> list[dict[str, object]]:
    """Return field failure counts sorted from highest to lowest."""

    counts = Counter(
        (row.get("field") or row.get("column") or "Unknown field").strip()
        for row in failures
    )
    return [
        {"field": field, "failure_count": count}
        for field, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _window(now: datetime | None, window_minutes: int) -> tuple[datetime, datetime]:
    if window_minutes <= 0:
        raise ValueError("window_minutes must be greater than zero")
    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(
        second=0, microsecond=0
    )
    return end - timedelta(minutes=window_minutes - 1), end


def _minutes(start: datetime, end: datetime) -> list[datetime]:
    count = int((end - start).total_seconds() // 60)
    return [start + timedelta(minutes=index) for index in range(count + 1)]


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


def _as_binary(value: str | None) -> int:
    try:
        return int(value or "")
    except ValueError:
        return 0
