"""Tests for data cleaning functionality."""

import numpy as np
import pandas as pd
import pytest

from factor_crowding.data.clean import DataCleaner


@pytest.fixture
def sample_prices():
    """Create sample price series."""
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    prices = pd.Series(100 * (1 + np.random.randn(100).cumsum() * 0.01), index=dates)
    return prices


def test_compute_returns(sample_prices):
    """Test return computation."""
    cleaner = DataCleaner()
    returns = cleaner.compute_returns(sample_prices)

    assert len(returns) == len(sample_prices)
    assert pd.isna(returns.iloc[0])  # First return should be NaN
    assert not pd.isna(returns.iloc[1])  # Second should be valid


def test_compute_log_returns(sample_prices):
    """Test log return computation."""
    cleaner = DataCleaner()
    log_returns = cleaner.compute_log_returns(sample_prices)

    assert len(log_returns) == len(sample_prices)
    assert pd.isna(log_returns.iloc[0])


def test_align_calendars():
    """Test calendar alignment."""
    cleaner = DataCleaner()

    # Create two dataframes with different date ranges
    dates1 = pd.date_range("2020-01-01", periods=50, freq="D")
    dates2 = pd.date_range("2020-01-15", periods=50, freq="D")

    df1 = pd.DataFrame({"a": range(50)}, index=dates1)
    df2 = pd.DataFrame({"b": range(50)}, index=dates2)

    # Inner join should give overlapping dates
    aligned1, aligned2 = cleaner.align_calendars(df1, df2, method="inner")

    assert len(aligned1) == len(aligned2)
    assert len(aligned1) < len(df1)
    assert len(aligned1) < len(df2)


def test_align_calendars_outer():
    """Test outer join alignment."""
    cleaner = DataCleaner()

    dates1 = pd.date_range("2020-01-01", periods=30, freq="D")
    dates2 = pd.date_range("2020-01-15", periods=30, freq="D")

    df1 = pd.DataFrame({"a": range(30)}, index=dates1)
    df2 = pd.DataFrame({"b": range(30)}, index=dates2)

    aligned1, aligned2 = cleaner.align_calendars(df1, df2, method="outer")

    # Should have union of dates
    assert len(aligned1) == len(aligned2)
    assert len(aligned1) >= max(len(df1), len(df2))
