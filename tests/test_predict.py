"""Tests for predictive modeling."""

import numpy as np
import pandas as pd
import pytest

from factor_crowding.models.predict import CrashPredictor


@pytest.fixture
def sample_data():
    """Create sample data for modeling."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=500, freq="D")

    data = pd.DataFrame(
        {
            "Mom": np.random.randn(500) * 0.01,
            "Mkt-RF": np.random.randn(500) * 0.01,
            "VIX": 15 + np.random.randn(500) * 5,
        },
        index=dates,
    )

    crowding_index = pd.Series(np.random.randn(500), index=dates, name="crowding")

    # Create some crash events
    crash_flags = pd.Series(False, index=dates)
    crash_flags.iloc[[50, 150, 300, 450]] = True

    return data, crowding_index, crash_flags


def test_prepare_predictive_dataset(sample_data):
    """Test preparation of predictive dataset."""
    master_data, crowding_index, crash_flags = sample_data
    predictor = CrashPredictor()

    pred_data = predictor.prepare_predictive_dataset(
        master_data, crowding_index, crash_flags, forward_window=5
    )

    assert not pred_data.empty
    assert "crowding_index" in pred_data.columns
    assert "crash_target" in pred_data.columns
    assert "vix" in pred_data.columns

    # Target should be binary
    assert set(pred_data["crash_target"].unique()).issubset({0, 1})


def test_conditional_analysis():
    """Test conditional analysis by crowding bins."""
    predictor = CrashPredictor()

    # Create sample data
    data = pd.DataFrame(
        {
            "crowding_index": np.random.randn(1000),
            "crash_target": np.random.choice([0, 1], 1000, p=[0.95, 0.05]),
        }
    )

    stats = predictor.conditional_analysis(data, n_bins=10)

    assert isinstance(stats, pd.DataFrame)
    assert len(stats) <= 10  # Should have up to 10 bins


def test_fit_logistic_model(sample_data):
    """Test logistic regression fitting."""
    master_data, crowding_index, crash_flags = sample_data
    predictor = CrashPredictor()

    # Prepare data
    pred_data = predictor.prepare_predictive_dataset(
        master_data, crowding_index, crash_flags, forward_window=5
    )

    X = pred_data.drop(columns=["crash_target"])
    y = pred_data["crash_target"]

    # Only test if we have both classes
    if len(y.unique()) > 1:
        results = predictor.fit_logistic_model(X, y, test_size=0.3)

        assert "model" in results
        assert "train_auc" in results
        assert "test_auc" in results
        assert "coefficients" in results

        # AUC should be between 0 and 1
        assert 0 <= results["train_auc"] <= 1
        assert 0 <= results["test_auc"] <= 1
