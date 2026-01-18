"""Tests for drawdown analysis."""

import numpy as np
import pandas as pd
import pytest

from factor_crowding.analysis.drawdowns import DrawdownAnalyzer


@pytest.fixture
def sample_returns():
    """Create sample return series with a known drawdown."""
    # Create returns that result in a drawdown
    returns = [0.01] * 50 + [-0.02] * 25 + [0.01] * 25
    dates = pd.date_range("2020-01-01", periods=len(returns), freq="D")
    return pd.Series(returns, index=dates)


def test_compute_cumulative_returns(sample_returns):
    """Test cumulative returns computation."""
    analyzer = DrawdownAnalyzer()
    cum_returns = analyzer.compute_cumulative_returns(sample_returns)

    assert len(cum_returns) == len(sample_returns)
    assert cum_returns.iloc[0] == 1 + sample_returns.iloc[0]
    assert cum_returns.iloc[-1] > 0


def test_compute_running_max(sample_returns):
    """Test running maximum computation."""
    analyzer = DrawdownAnalyzer()
    cum_returns = analyzer.compute_cumulative_returns(sample_returns)
    running_max = analyzer.compute_running_max(cum_returns)

    assert len(running_max) == len(cum_returns)
    # Running max should be monotonically non-decreasing
    assert (running_max.diff().dropna() >= -1e-10).all()


def test_compute_drawdown(sample_returns):
    """Test drawdown computation."""
    analyzer = DrawdownAnalyzer()
    drawdown = analyzer.compute_drawdown(sample_returns)

    assert len(drawdown) == len(sample_returns)
    # Drawdowns should be non-positive
    assert (drawdown <= 0).all()


def test_compute_max_drawdown(sample_returns):
    """Test maximum drawdown calculation."""
    analyzer = DrawdownAnalyzer()
    max_dd = analyzer.compute_max_drawdown(sample_returns)

    assert max_dd <= 0
    assert isinstance(max_dd, (float, np.floating))


def test_identify_crash_events():
    """Test crash event identification."""
    analyzer = DrawdownAnalyzer(crash_percentile=5.0)

    # Create returns with some extreme negatives
    np.random.seed(42)
    returns = pd.Series(np.random.randn(1000) * 0.01)
    returns.iloc[100] = -0.05  # Add crash
    returns.iloc[500] = -0.06  # Add another crash

    crashes = analyzer.identify_crash_events(returns, window=1)

    assert isinstance(crashes, pd.Series)
    assert crashes.dtype == bool
    assert crashes.sum() > 0  # Should identify some crashes


def test_compute_drawdown_episodes(sample_returns):
    """Test drawdown episode identification."""
    analyzer = DrawdownAnalyzer(drawdown_threshold=1.0)
    episodes = analyzer.compute_drawdown_episodes(sample_returns)

    assert isinstance(episodes, pd.DataFrame)

    if not episodes.empty:
        assert "start_date" in episodes.columns
        assert "trough_date" in episodes.columns
        assert "end_date" in episodes.columns
        assert "depth_pct" in episodes.columns
        assert "duration_days" in episodes.columns


def test_drawdown_always_negative_or_zero():
    """Test that drawdowns are always <= 0."""
    analyzer = DrawdownAnalyzer()

    # Various return patterns
    patterns = [
        pd.Series([0.01] * 100),  # All positive
        pd.Series([-0.01] * 100),  # All negative
        pd.Series(np.random.randn(100) * 0.01),  # Random
    ]

    for returns in patterns:
        drawdown = analyzer.compute_drawdown(returns)
        assert (drawdown <= 1e-10).all(), "Drawdown should be non-positive"
