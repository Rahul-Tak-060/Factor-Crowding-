"""Data download module for fetching factor, market, and ETF data."""

import io
import zipfile
from pathlib import Path

import pandas as pd
import pandas_datareader.data as web
import requests
import yfinance as yf
from tqdm import tqdm

from factor_crowding.config import data_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)


class DataDownloader:
    """Download and cache financial data from various sources."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the data downloader.

        Args:
            cache_dir: Directory to cache downloaded data. Defaults to config.
        """
        self.cache_dir = cache_dir or data_config.raw_data_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_fama_french_daily(
        self, force_refresh: bool = False
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Download daily Fama-French factors including momentum.

        Args:
            force_refresh: If True, re-download even if cached.

        Returns:
            Tuple of (main_factors_df, momentum_df)
        """
        logger.info("Downloading Fama-French daily factors...")

        # Download main factors (Mkt-RF, SMB, HML, RF)
        main_factors_file = self.cache_dir / "ff_daily_factors.csv"
        if not main_factors_file.exists() or force_refresh:
            main_factors = self._download_ff_zip(data_config.ff_daily_url, "Fama/French 3 Factors")
            main_factors.to_csv(main_factors_file)
            logger.info(f"Saved main factors to {main_factors_file}")
        else:
            main_factors = pd.read_csv(main_factors_file, index_col=0, parse_dates=True)
            logger.info("Loaded main factors from cache")

        # Download momentum factor
        momentum_file = self.cache_dir / "ff_daily_momentum.csv"
        if not momentum_file.exists() or force_refresh:
            momentum = self._download_ff_zip(data_config.ff_mom_daily_url, "Momentum Factor")
            momentum.to_csv(momentum_file)
            logger.info(f"Saved momentum factor to {momentum_file}")
        else:
            momentum = pd.read_csv(momentum_file, index_col=0, parse_dates=True)
            logger.info("Loaded momentum factor from cache")

        return main_factors, momentum

    def _download_ff_zip(self, url: str, sheet_name: str) -> pd.DataFrame:
        """Download and parse a Fama-French zip file.

        Args:
            url: URL to the zip file
            sheet_name: Name of the data series

        Returns:
            DataFrame with parsed factor returns
        """
        logger.info(f"Fetching {sheet_name} from {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            csv_name = zip_file.namelist()[0]
            with zip_file.open(csv_name) as csv_file:
                # Read all lines to find where data starts
                csv_file.seek(0)
                lines = [
                    line.decode("utf-8", errors="ignore").strip() for line in csv_file.readlines()
                ]

                # Find where actual data starts (first line that looks like a date: YYYYMMDD)
                data_start_idx = None
                for i, line in enumerate(lines):
                    # Look for a line that starts with 8 digits
                    parts = line.split(",")
                    if parts and len(parts[0].strip()) == 8 and parts[0].strip().isdigit():
                        data_start_idx = i
                        break

                if data_start_idx is None:
                    logger.warning(f"Could not find data start in {sheet_name}, using default")
                    data_start_idx = 3  # Fallback

                # Header is one line before data
                header_idx = max(0, data_start_idx - 1)

                # Read the CSV with proper header
                csv_file.seek(0)
                df = pd.read_csv(
                    csv_file, skiprows=range(0, header_idx) if header_idx > 0 else None
                )

                # Clean column names (remove whitespace)
                df.columns = df.columns.str.strip()

                # Find where the data ends (empty line, copyright, or non-numeric first column)
                first_col = df.iloc[:, 0].astype(str).str.strip()

                # Look for empty rows
                empty_idx = df[first_col == ""].index

                # Look for copyright or other footer text (non-numeric in first column)
                # Valid dates should be all digits (YYYYMMDD = 8 digits)
                non_date_idx = df[~first_col.str.match(r"^\d{8}$", na=False)].index

                # Use the earliest stopping point (convert to integer position)
                all_stop_points = []
                if len(empty_idx) > 0:
                    all_stop_points.append(df.index.get_loc(empty_idx[0]))
                if len(non_date_idx) > 0:
                    all_stop_points.append(df.index.get_loc(non_date_idx[0]))

                if all_stop_points:
                    df = df.iloc[: min(all_stop_points)]

                # Set date as index
                df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%Y%m%d")
                df.set_index(df.columns[0], inplace=True)

                # Convert to numeric (they're in percentage points, will convert later)
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                logger.info(f"Downloaded {len(df)} rows for {sheet_name}")
                return df

    def download_vix(
        self, start_date: str = "1990-01-01", force_refresh: bool = False
    ) -> pd.DataFrame:
        """Download VIX daily close data from FRED.

        Args:
            start_date: Start date for download (YYYY-MM-DD)
            force_refresh: If True, re-download even if cached.

        Returns:
            DataFrame with VIX daily close values
        """
        logger.info(f"Downloading VIX from FRED starting {start_date}...")

        vix_file = self.cache_dir / "vix_daily.csv"
        if not vix_file.exists() or force_refresh:
            vix = web.DataReader(data_config.vix_series, "fred", start=start_date, end=None)
            vix.to_csv(vix_file)
            logger.info(f"Saved VIX to {vix_file}")
        else:
            vix = pd.read_csv(vix_file, index_col=0, parse_dates=True)
            logger.info("Loaded VIX from cache")

        return vix

    def download_etf_data(
        self,
        tickers: list[str] | None = None,
        start_date: str = "2010-01-01",
        force_refresh: bool = False,
    ) -> dict[str, pd.DataFrame]:
        """Download ETF OHLCV data from Yahoo Finance.

        Args:
            tickers: List of ETF tickers. Defaults to config.
            start_date: Start date for download (YYYY-MM-DD)
            force_refresh: If True, re-download even if cached.

        Returns:
            Dictionary mapping ticker to OHLCV DataFrame
        """
        tickers = tickers or data_config.etf_tickers
        logger.info(f"Downloading ETF data for {tickers}...")

        etf_data = {}
        for ticker in tqdm(tickers, desc="Downloading ETFs"):
            etf_file = self.cache_dir / f"{ticker}_daily.csv"

            if not etf_file.exists() or force_refresh:
                try:
                    df = yf.download(ticker, start=start_date, progress=False, auto_adjust=False)
                    if df.empty:
                        logger.warning(f"No data returned for {ticker}")
                        continue

                    # Flatten multi-level columns if necessary
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    # Ensure index is datetime and save with proper format
                    df.index = pd.to_datetime(df.index)
                    df.index.name = "Date"
                    df.to_csv(etf_file, date_format="%Y-%m-%d")
                    logger.info(f"Saved {ticker} to {etf_file}")
                    etf_data[ticker] = df
                except Exception as e:
                    logger.error(f"Failed to download {ticker}: {e}")
            else:
                # Load with explicit parsing
                df = pd.read_csv(etf_file, index_col=0, parse_dates=["Date"])
                if df.index.dtype == "object":
                    df.index = pd.to_datetime(df.index, format="%Y-%m-%d")
                df.index.name = "Date"
                logger.info(f"Loaded {ticker} from cache")
                etf_data[ticker] = df

        return etf_data

    def download_all(self, start_date: str = "2010-01-01", force_refresh: bool = False) -> None:
        """Download all required datasets.

        Args:
            start_date: Start date for time series data
            force_refresh: If True, re-download all data
        """
        logger.info("Starting full data download...")

        # Download Fama-French factors
        self.download_fama_french_daily(force_refresh=force_refresh)

        # Download VIX
        self.download_vix(start_date=start_date, force_refresh=force_refresh)

        # Download ETF data
        self.download_etf_data(start_date=start_date, force_refresh=force_refresh)

        logger.info("Data download complete!")


if __name__ == "__main__":
    # Example usage
    downloader = DataDownloader()
    downloader.download_all(start_date="2010-01-01", force_refresh=False)
