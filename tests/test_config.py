"""Tests for configuration module."""

from pathlib import Path

from factor_crowding.config import AnalysisConfig, DataConfig, LoggingConfig


def test_data_config_initialization():
    """Test DataConfig initializes correctly."""
    config = DataConfig()

    assert isinstance(config.base_dir, Path)
    assert isinstance(config.data_dir, Path)
    assert isinstance(config.raw_data_dir, Path)
    assert isinstance(config.processed_data_dir, Path)

    # Check default tickers
    assert "MTUM" in config.etf_tickers
    assert "VLUE" in config.etf_tickers
    assert "USMV" in config.etf_tickers

    # Check FF factors
    assert "Mom" in config.ff_factors
    assert "Mkt-RF" in config.ff_factors


def test_analysis_config():
    """Test AnalysisConfig default values."""
    config = AnalysisConfig()

    assert config.short_window == 63
    assert config.medium_window == 126
    assert config.long_window == 252
    assert config.crash_percentile == 1.0
    assert config.random_seed == 42


def test_logging_config():
    """Test LoggingConfig."""
    config = LoggingConfig()

    assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert "factor_crowding" in config.log_file
