"""Data cleaning and preprocessing module."""

from pathlib import Path

import numpy as np
import pandas as pd

from factor_crowding.config import data_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)


class DataCleaner:
    """Clean and align financial data from multiple sources."""

    def __init__(
        self,
        raw_data_dir: Path | None = None,
        processed_data_dir: Path | None = None,
    ):
        """Initialize the data cleaner.

        Args:
            raw_data_dir: Directory containing raw data files
            processed_data_dir: Directory to save processed data
        """
        self.raw_data_dir = raw_data_dir or data_config.raw_data_dir
        self.processed_data_dir = processed_data_dir or data_config.processed_data_dir
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def load_fama_french_factors(self) -> pd.DataFrame:
        """Load and combine Fama-French factors.

        Returns:
            DataFrame with all FF factors (Mkt-RF, SMB, HML, Mom, RF)
        """
        logger.info("Loading Fama-French factors...")

        # Load main factors
        main_factors = pd.read_csv(
            self.raw_data_dir / "ff_daily_factors.csv",
            index_col=0,
            parse_dates=True,
        )

        # Load momentum
        momentum = pd.read_csv(
            self.raw_data_dir / "ff_daily_momentum.csv",
            index_col=0,
            parse_dates=True,
        )

        # Combine
        ff_factors = main_factors.join(momentum, how="inner")

        # Convert from percentage points to decimal returns
        ff_factors = ff_factors / 100.0

        logger.info(f"Loaded FF factors: {ff_factors.shape}")
        return ff_factors

    def load_vix(self) -> pd.Series:
        """Load VIX data.

        Returns:
            Series with VIX daily close values
        """
        logger.info("Loading VIX data...")

        vix = pd.read_csv(
            self.raw_data_dir / "vix_daily.csv",
            index_col=0,
            parse_dates=True,
        )

        # Extract the series
        vix_series = vix.iloc[:, 0]
        vix_series.name = "VIX"

        logger.info(f"Loaded VIX: {len(vix_series)} observations")
        return vix_series

    def load_etf_data(self, tickers: list[str] | None = None) -> dict[str, pd.DataFrame]:
        """Load ETF data for specified tickers.

        Args:
            tickers: List of ETF tickers. Defaults to config.

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        tickers = tickers or data_config.etf_tickers
        logger.info(f"Loading ETF data for {tickers}...")

        etf_data = {}
        for ticker in tickers:
            file_path = self.raw_data_dir / f"{ticker}_daily.csv"
            if file_path.exists():
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                etf_data[ticker] = df
                logger.info(f"Loaded {ticker}: {df.shape}")
            else:
                logger.warning(f"File not found: {file_path}")

        return etf_data

    def compute_returns(self, prices: pd.Series) -> pd.Series:
        """Compute simple returns from prices.

        Args:
            prices: Series of prices

        Returns:
            Series of returns
        """
        return prices.pct_change(fill_method=None)

    def compute_log_returns(self, prices: pd.Series) -> pd.Series:
        """Compute log returns from prices.

        Args:
            prices: Series of prices

        Returns:
            Series of log returns
        """
        return np.log(prices / prices.shift(1))

    def align_calendars(
        self,
        *dataframes: pd.DataFrame,
        method: str = "inner",
        fill_method: str | None = None,
    ) -> tuple[pd.DataFrame, ...]:
        """Align multiple dataframes to a common date index.

        Args:
            *dataframes: Variable number of DataFrames to align
            method: Join method ('inner', 'outer', 'left', 'right')
            fill_method: Optional fill method for missing values ('ffill', 'bfill', None)

        Returns:
            Tuple of aligned DataFrames
        """
        logger.info(f"Aligning {len(dataframes)} dataframes with method '{method}'...")

        if len(dataframes) == 0:
            return ()
        if len(dataframes) == 1:
            return dataframes

        # Find common index
        common_index = dataframes[0].index
        for df in dataframes[1:]:
            if method == "inner":
                common_index = common_index.intersection(df.index)
            elif method == "outer":
                common_index = common_index.union(df.index)

        common_index = common_index.sort_values()

        # Reindex all dataframes
        result = []
        for df in dataframes:
            aligned_df = df.reindex(common_index)
            if fill_method:
                if fill_method == "ffill":
                    aligned_df = aligned_df.ffill()
                elif fill_method == "bfill":
                    aligned_df = aligned_df.bfill()
            result.append(aligned_df)

        logger.info(f"Aligned to {len(common_index)} common dates")
        return tuple(result)

    def create_master_dataset(self, start_date: str | None = None) -> pd.DataFrame:
        """Create a master dataset with all features aligned.

        Args:
            start_date: Optional start date to filter data

        Returns:
            Aligned DataFrame with all features
        """
        logger.info("Creating master dataset...")

        # Load all data
        ff_factors = self.load_fama_french_factors()
        vix = self.load_vix()
        etf_data = self.load_etf_data()

        # Compute ETF returns
        etf_returns = {}
        etf_volumes = {}
        for ticker, df in etf_data.items():
            # Use adjusted close for returns
            if "Close" in df.columns:
                close_col = "Close"
            elif "Adj Close" in df.columns:
                close_col = "Adj Close"
            else:
                logger.warning(f"No close price column found for {ticker}")
                continue

            # Ensure numeric type
            prices = pd.to_numeric(df[close_col], errors="coerce")
            etf_returns[ticker] = self.compute_returns(prices)

            if "Volume" in df.columns:
                etf_volumes[ticker] = pd.to_numeric(df["Volume"], errors="coerce")

        # Create DataFrames
        etf_returns_df = pd.DataFrame(etf_returns)
        etf_volumes_df = pd.DataFrame(etf_volumes)

        # Align all data
        vix_df = vix.to_frame()
        aligned_ff, aligned_vix, aligned_returns, aligned_volumes = self.align_calendars(
            ff_factors, vix_df, etf_returns_df, etf_volumes_df, method="inner"
        )

        # Combine into master dataset
        master = pd.concat(
            [
                aligned_ff,
                aligned_vix,
                aligned_returns.add_suffix("_ret"),
                aligned_volumes.add_suffix("_vol"),
            ],
            axis=1,
        )

        # Filter by start date if provided
        if start_date:
            master = master[master.index >= start_date]
            logger.info(f"Filtered data from {start_date}")

        # Drop rows with any NaN (from return computation or missing data)
        initial_len = len(master)
        master = master.dropna()
        logger.info(f"Dropped {initial_len - len(master)} rows with missing values")

        logger.info(f"Master dataset created: {master.shape}")

        # Save processed data
        output_file = self.processed_data_dir / "master_dataset.csv"
        master.to_csv(output_file)
        logger.info(f"Saved master dataset to {output_file}")

        return master


if __name__ == "__main__":
    # Example usage
    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date="2010-01-01")
    print(master_df.head())
    print(f"\nColumns: {master_df.columns.tolist()}")
