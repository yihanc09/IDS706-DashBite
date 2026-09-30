import pytest

from dashboard.app import _chart_rows, _flag_title, _volume_title


@pytest.mark.regression
def test_dashboard_titles_state_findings():
    assert "Orders are arriving" in _volume_title(
        [{"minute": "now", "sample_count": 3}]
    )
    assert "flagging" in _flag_title(
        [{"minute": "earlier", "flag_rate": 0.1}, {"minute": "now", "flag_rate": 0.2}]
    )


@pytest.mark.regression
def test_dashboard_encodes_flag_rate_as_percent_and_handles_empty_flags():
    assert _chart_rows(
        [{"minute": "now", "flag_rate": 0.25}], "minute", "flag_rate", scale=100
    ) == [{"minute": "now", "flag_rate": 25.0}]
    assert "has not flagged" in _flag_title(
        [{"minute": "earlier", "flag_rate": 0.0}]
    )
