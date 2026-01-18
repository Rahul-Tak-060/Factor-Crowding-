"""Tests for crowding index computation."""

import numpy as np
import pandas as pd
import pytest

from factor_crowding.features.crowding import CrowdingIndexBuilder


@pytest.fixture
def sample_returns():
    """Create sample return data."""
    dates = pd.date_range("2020-01-01", periods=300, freq="D")
    returns = pd.DataFrame(
        {
            "MTUM_ret": np.random.randn(300) * 0.01,
            "VLUE_ret": np.random.randn(300) * 0.01,
            "USMV_ret": np.random.randn(300) * 0.01,
        },
        index=dates,
    )
    return returns


@pytest.fixture
def sample_volumes():
    """Create sample volume data."""
    dates = pd.date_range("2020-01-01", periods=300, freq="D")
    volumes = pd.DataFrame(
        {
            "MTUM_vol": np.random.randint(1000000, 10000000, 300),
            "VLUE_vol": np.random.randint(1000000, 10000000, 300),
            "USMV_vol": np.random.randint(1000000, 10000000, 300),
        },
        index=dates,
    )
    return volumes


def test_compute_zscore():
    """Test z-score computation."""
    builder = CrowdingIndexBuilder()

    series = pd.Series(range(100))
    zscore = builder.compute_zscore(series, window=20)

    assert len(zscore) == len(series)
    # Most values should be within reasonable z-score range
    assert zscore.dropna().abs().mean() < 2


def test_winsorize_series():
    """Test series winsorization."""
    builder = CrowdingIndexBuilder()

    # Create series with outliers
    series = pd.Series(np.concatenate([np.random.randn(98), [100, -100]]))
    winsorized = builder.winsorize_series(series)

    # Extreme values should be capped
    assert winsorized.max() < 100
    assert winsorized.min() > -100


def test_build_comovement_proxy(sample_returns):
    """Test co-movement proxy construction."""
    builder = CrowdingIndexBuilder()

    comovement = builder.build_comovement_proxy(sample_returns)

    assert not comovement.empty
    assert "avg_corr" in comovement.columns

    # Correlations should be between -1 and 1
    assert comovement["avg_corr"].dropna().abs().max() <= 1


def test_build_flow_attention_proxy(sample_returns, sample_volumes):
    """Test flow-attention proxy construction."""
    builder = CrowdingIndexBuilder()

    flow_attention = builder.build_flow_attention_proxy(sample_returns, sample_volumes)

    assert not flow_attention.empty
    # Should have volume z-scores
    vol_cols = [col for col in flow_attention.columns if "vol_zscore" in col]
    assert len(vol_cols) > 0


def test_build_factor_side_proxy():
    """Test factor-side proxy construction."""
    builder = CrowdingIndexBuilder()

    # Create sample factor returns
    dates = pd.date_range("2020-01-01", periods=300, freq="D")
    factor_returns = pd.DataFrame(
        {
            "Mom": np.random.randn(300) * 0.01,
            "HML": np.random.randn(300) * 0.01,
        },
        index=dates,
    )

    factor_proxy = builder.build_factor_side_proxy(factor_returns)

    assert not factor_proxy.empty
    # Should have volatility z-scores
    vol_cols = [col for col in factor_proxy.columns if "vol_zscore" in col]
    assert len(vol_cols) > 0


def test_build_composite_index(sample_returns, sample_volumes):
    """Test composite index construction."""
    builder = CrowdingIndexBuilder()

    comovement = builder.build_comovement_proxy(sample_returns)
    flow_attention = builder.build_flow_attention_proxy(sample_returns, sample_volumes)

    composite = builder.build_composite_index(comovement, flow_attention)

    assert isinstance(composite, pd.Series)
    assert len(composite) == len(sample_returns)
