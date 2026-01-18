"""Configuration module for factor crowding analysis.

This module contains all configuration parameters, file paths, and constants
used throughout the project.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DataConfig:
    """Data source and path configuration."""

    # Directories
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(init=False)
    raw_data_dir: Path = field(init=False)
    processed_data_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    # Tickers
    etf_tickers: list[str] = field(default_factory=lambda: ["MTUM", "VLUE", "USMV"])

    # Fama-French factors
    ff_factors: list[str] = field(default_factory=lambda: ["Mkt-RF", "SMB", "HML", "Mom", "RF"])

    # FRED series
    vix_series: str = "VIXCLS"

    # URLs
    ff_daily_url: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
        "ftp/F-F_Research_Data_Factors_daily_CSV.zip"
    )
    ff_mom_daily_url: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
        "ftp/F-F_Momentum_Factor_daily_CSV.zip"
    )

    def __post_init__(self) -> None:
        """Initialize directory paths."""
        self.data_dir = self.base_dir / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.output_dir = self.base_dir / "outputs"
        self.figures_dir = self.output_dir / "figures"
        self.logs_dir = self.base_dir / "logs"

        # Create directories if they don't exist
        for directory in [
            self.raw_data_dir,
            self.processed_data_dir,
            self.figures_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class AnalysisConfig:
    """Analysis parameters and thresholds."""

    # Rolling window sizes (trading days)
    short_window: int = 63  # ~3 months
    medium_window: int = 126  # ~6 months
    long_window: int = 252  # ~1 year

    # Percentile thresholds
    crash_percentile: float = 1.0  # 1st percentile for crash definition
    high_stress_percentile: float = 75.0  # VIX 75th percentile
    low_stress_percentile: float = 25.0  # VIX 25th percentile

    # Winsorization limits for crowding index
    winsorize_lower: float = 1.0  # 1st percentile
    winsorize_upper: float = 99.0  # 99th percentile

    # Drawdown threshold for episode detection
    drawdown_threshold_pct: float = 5.0  # 5% drawdown

    # Forward return windows for prediction
    forward_windows: list[int] = field(default_factory=lambda: [5, 20])  # 5d, 20d

    # Random seed for reproducibility
    random_seed: int = 42


@dataclass
class LoggingConfig:
    """Logging configuration."""

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/factor_crowding.log"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


# Global configuration instances
data_config = DataConfig()
analysis_config = AnalysisConfig()
logging_config = LoggingConfig()
