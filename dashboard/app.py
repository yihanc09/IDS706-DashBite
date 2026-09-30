"""Sparse, claim-first Model Pulse dashboard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from pipeline.paths import DATA_ROOT
from pipeline.pulse import (
    field_failure_counts,
    late_flag_rate_over_time,
    read_csv,
    score_summary,
    sample_volume,
    volume_over_time,
)


FEATURES_PATH = DATA_ROOT / "features" / "features.csv"
PREDICTIONS_PATH = DATA_ROOT / "predictions" / "predictions.csv"
QUALITY_PATH = DATA_ROOT / "quality" / "quality.csv"


def main() -> None:
    st.set_page_config(page_title="Model Pulse", layout="wide")
    st.title("Model Pulse")
    st.caption("A read-only view of late-order model health")

    features = read_csv(FEATURES_PATH)
    predictions = read_csv(PREDICTIONS_PATH)
    failures = read_csv(QUALITY_PATH)
    summary = score_summary(predictions)
    volume = sample_volume(features)
    drop_rate = len(failures) / (volume + len(failures)) if volume else 0.0

    kpi_columns = st.columns(3)
    kpi_columns[0].metric("Samples observed", volume)
    kpi_columns[1].metric("Drop rate", f"{drop_rate:.1%}")
    kpi_columns[2].metric("Orders flagged late", f"{summary['late_flag_rate']:.1%}")

    volume_series = volume_over_time(features)
    st.subheader(_volume_title(volume_series))
    st.line_chart(
        _chart_rows(volume_series, "minute", "sample_count"),
        x="minute",
        y="sample_count",
        y_label="Orders",
    )

    flag_series = late_flag_rate_over_time(features, predictions)
    st.subheader(_flag_title(flag_series))
    st.line_chart(
        _chart_rows(flag_series, "minute", "flag_rate", scale=100),
        x="minute",
        y="flag_rate",
        y_label="% flagged late",
    )

    st.subheader("These fields account for the most dropped rows")
    failures_by_field = field_failure_counts(failures)
    if failures_by_field:
        st.bar_chart(
            _chart_rows(failures_by_field, "field", "failure_count"),
            x="field",
            y="failure_count",
            horizontal=True,
            y_label="Dropped rows",
        )
    else:
        st.info("No field failures have been recorded yet.")


def _chart_rows(
    rows: list[dict[str, object]],
    x: str,
    y: str,
    *,
    scale: int = 1,
) -> list[dict[str, object]]:
    return [{x: row[x], y: float(row[y]) * scale} for row in rows]


def _volume_title(series: list[dict[str, object]]) -> str:
    total = sum(int(row["sample_count"]) for row in series)
    return f"Orders are arriving steadily ({total} in the recent window)"


def _flag_title(series: list[dict[str, object]]) -> str:
    non_empty = [float(row["flag_rate"]) for row in series]
    if not any(non_empty):
        return "The model has not flagged any late orders yet"
    if len(non_empty) >= 2 and non_empty[-1] > non_empty[0]:
        return "The model is flagging more late orders"
    if len(non_empty) >= 2 and non_empty[-1] < non_empty[0]:
        return "The model is flagging fewer late orders"
    return "The model is holding its late-order flag rate steady"


if __name__ == "__main__":
    main()
