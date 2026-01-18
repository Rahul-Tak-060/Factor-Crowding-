"""Crowding index computation module.

This module implements three approaches to measuring factor crowding:
A) Flow-attention proxy (ETF volume and price momentum)
B) Co-movement proxy (rolling correlations among factor ETFs)
C) Factor-side proxy (volatility and autocorrelation of factor returns)
"""


import numpy as np
import pandas as pd
from scipy.stats import mstats

from factor_crowding.config import analysis_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)


class CrowdingIndexBuilder:
    """Build crowding indices from ETF and factor data."""

    def __init__(
        self,
        short_window: int = analysis_config.short_window,
        medium_window: int = analysis_config.medium_window,
        long_window: int = analysis_config.long_window,
        winsorize_lower: float = analysis_config.winsorize_lower,
        winsorize_upper: float = analysis_config.winsorize_upper,
    ):
        """Initialize the crowding index builder.

        Args:
            short_window: Short rolling window (e.g., 63 days)
            medium_window: Medium rolling window (e.g., 126 days)
            long_window: Long rolling window (e.g., 252 days)
            winsorize_lower: Lower percentile for winsorization
            winsorize_upper: Upper percentile for winsorization
        """
        self.short_window = short_window
        self.medium_window = medium_window
        self.long_window = long_window
        self.winsorize_lower = winsorize_lower
        self.winsorize_upper = winsorize_upper

    def compute_zscore(
        self, series: pd.Series, window: int, min_periods: int | None = None
    ) -> pd.Series:
        """Compute rolling z-score.

        Args:
            series: Input series
            window: Rolling window size
            min_periods: Minimum number of observations

        Returns:
            Rolling z-score series
        """
        if min_periods is None:
            min_periods = window // 2

        rolling_mean = series.rolling(window=window, min_periods=min_periods).mean()
        rolling_std = series.rolling(window=window, min_periods=min_periods).std()

        # Avoid division by zero
        zscore = (series - rolling_mean) / rolling_std.replace(0, np.nan)
        return zscore

    def winsorize_series(self, series: pd.Series) -> pd.Series:
        """Winsorize a series at specified percentiles.

        Args:
            series: Input series

        Returns:
            Winsorized series
        """
        limits = (self.winsorize_lower / 100, (100 - self.winsorize_upper) / 100)
        winsorized = pd.Series(
            mstats.winsorize(series.dropna(), limits=limits),
            index=series.dropna().index,
        )
        return series.combine_first(winsorized)

    def build_flow_attention_proxy(
        self, returns: pd.DataFrame, volumes: pd.DataFrame
    ) -> pd.DataFrame:
        """Build flow-attention crowding proxy (Proxy Set A).

        Combines:
        - Volume z-score (short window)
        - Return run-up z-score (medium window)
        - Crash frequency (short window)

        Args:
            returns: DataFrame of ETF returns
            volumes: DataFrame of ETF volumes

        Returns:
            DataFrame with crowding components for each ETF
        """
        logger.info("Building flow-attention crowding proxy...")

        components = pd.DataFrame(index=returns.index)

        for ticker in returns.columns:
            if ticker.endswith("_ret"):
                ticker_name = ticker.replace("_ret", "")
                vol_col = f"{ticker_name}_vol"

                if vol_col in volumes.columns:
                    # Volume z-score
                    vol_zscore = self.compute_zscore(volumes[vol_col], self.short_window)
                    components[f"{ticker_name}_vol_zscore"] = vol_zscore

                # Return run-up z-score (cumulative return over medium window)
                cum_return = (
                    (1 + returns[ticker])
                    .rolling(self.medium_window)
                    .apply(lambda x: x.prod() - 1, raw=True)
                )
                ret_zscore = self.compute_zscore(cum_return, self.medium_window)
                components[f"{ticker_name}_ret_zscore"] = ret_zscore

                # Crash frequency (negative skew proxy)
                # Count of large down days in short window
                crash_threshold = returns[ticker].quantile(0.05)
                crash_days = (returns[ticker] < crash_threshold).astype(int)
                crash_freq = crash_days.rolling(self.short_window).sum()
                crash_freq_zscore = self.compute_zscore(crash_freq, self.short_window)
                components[f"{ticker_name}_crash_freq"] = crash_freq_zscore

        logger.info(f"Flow-attention proxy created with {len(components.columns)} components")
        return components

    def build_comovement_proxy(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Build co-movement crowding proxy (Proxy Set B).

        Computes rolling correlations among factor ETF returns.

        Args:
            returns: DataFrame of ETF returns

        Returns:
            DataFrame with correlation-based crowding measures
        """
        logger.info("Building co-movement crowding proxy...")

        # Get ETF return columns
        etf_cols = [col for col in returns.columns if col.endswith("_ret")]
        etf_returns = returns[etf_cols]

        if len(etf_cols) < 2:
            logger.warning("Need at least 2 ETFs for correlation proxy")
            return pd.DataFrame(index=returns.index)

        components = pd.DataFrame(index=returns.index)

        # Pairwise correlations
        pairs = []
        for i, col1 in enumerate(etf_cols):
            for col2 in etf_cols[i + 1 :]:
                ticker1 = col1.replace("_ret", "")
                ticker2 = col2.replace("_ret", "")
                pair_name = f"corr_{ticker1}_{ticker2}"

                # Rolling correlation
                rolling_corr = etf_returns[col1].rolling(self.medium_window).corr(etf_returns[col2])
                components[pair_name] = rolling_corr
                pairs.append(pair_name)

        # Average correlation
        if pairs:
            components["avg_corr"] = components[pairs].mean(axis=1)

        logger.info(f"Co-movement proxy created with {len(components.columns)} components")
        return components

    def build_factor_side_proxy(self, factor_returns: pd.DataFrame) -> pd.DataFrame:
        """Build factor-side crowding proxy (Proxy Set C).

        Uses factor return characteristics:
        - Rolling volatility
        - Rolling autocorrelation

        Args:
            factor_returns: DataFrame of Fama-French factor returns

        Returns:
            DataFrame with factor-side crowding measures
        """
        logger.info("Building factor-side crowding proxy...")

        components = pd.DataFrame(index=factor_returns.index)

        for factor in factor_returns.columns:
            if factor == "RF":  # Skip risk-free rate
                continue

            # Rolling volatility
            rolling_vol = factor_returns[factor].rolling(self.short_window).std()
            vol_zscore = self.compute_zscore(rolling_vol, self.medium_window)
            components[f"{factor}_vol_zscore"] = vol_zscore

            # Rolling autocorrelation (1-day lag)
            rolling_autocorr = (
                factor_returns[factor]
                .rolling(self.short_window)
                .apply(lambda x: x.autocorr(lag=1), raw=False)
            )
            autocorr_zscore = self.compute_zscore(rolling_autocorr, self.medium_window)
            components[f"{factor}_autocorr_zscore"] = autocorr_zscore

        logger.info(f"Factor-side proxy created with {len(components.columns)} components")
        return components

    def build_composite_index(
        self,
        *component_dfs: pd.DataFrame,
        winsorize: bool = True,
    ) -> pd.Series:
        """Combine multiple component DataFrames into a composite crowding index.

        Args:
            *component_dfs: Variable number of component DataFrames
            winsorize: Whether to winsorize the final index

        Returns:
            Composite crowding index as Series
        """
        logger.info("Building composite crowding index...")

        # Combine all components
        all_components = pd.concat(component_dfs, axis=1)

        # Compute mean across all components
        composite = all_components.mean(axis=1, skipna=True)

        # Winsorize
        if winsorize:
            composite = self.winsorize_series(composite)

        logger.info(f"Composite index created from {len(all_components.columns)} components")
        return composite

    def build_all_crowding_indices(self, master_data: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Build all three crowding proxy sets and composite index.

        Args:
            master_data: Master dataset with all features

        Returns:
            Dictionary with all crowding components and indices
        """
        logger.info("Building all crowding indices...")

        results = {}

        # Extract relevant columns
        etf_return_cols = [col for col in master_data.columns if col.endswith("_ret")]
        etf_volume_cols = [col for col in master_data.columns if col.endswith("_vol")]
        factor_cols = ["Mkt-RF", "SMB", "HML", "Mom"]  # Exclude RF

        etf_returns = master_data[etf_return_cols]
        etf_volumes = master_data[etf_volume_cols]
        factor_returns = master_data[[col for col in factor_cols if col in master_data.columns]]

        # Build each proxy set
        if not etf_returns.empty and not etf_volumes.empty:
            results["flow_attention"] = self.build_flow_attention_proxy(etf_returns, etf_volumes)
        else:
            logger.warning("Insufficient ETF data for flow-attention proxy")
            results["flow_attention"] = pd.DataFrame(index=master_data.index)

        if not etf_returns.empty:
            results["comovement"] = self.build_comovement_proxy(etf_returns)
        else:
            logger.warning("Insufficient ETF data for co-movement proxy")
            results["comovement"] = pd.DataFrame(index=master_data.index)

        if not factor_returns.empty:
            results["factor_side"] = self.build_factor_side_proxy(factor_returns)
        else:
            logger.warning("Insufficient factor data for factor-side proxy")
            results["factor_side"] = pd.DataFrame(index=master_data.index)

        # Build composite indices
        # Composite A: Flow-attention only
        if not results["flow_attention"].empty:
            results["crowding_index_a"] = self.build_composite_index(
                results["flow_attention"]
            ).to_frame("CrowdingIndex_A")

        # Composite B: Co-movement only
        if not results["comovement"].empty:
            results["crowding_index_b"] = self.build_composite_index(
                results["comovement"]
            ).to_frame("CrowdingIndex_B")

        # Composite C: Factor-side only
        if not results["factor_side"].empty:
            results["crowding_index_c"] = self.build_composite_index(
                results["factor_side"]
            ).to_frame("CrowdingIndex_C")

        # Composite ALL: Combined
        non_empty = [df for df in results.values() if isinstance(df, pd.DataFrame) and not df.empty]
        if non_empty:
            results["crowding_index_all"] = self.build_composite_index(*non_empty).to_frame(
                "CrowdingIndex_All"
            )

        logger.info("All crowding indices built successfully")
        return results


if __name__ == "__main__":
    # Example usage - would need master dataset
    from factor_crowding.data.clean import DataCleaner

    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date="2010-01-01")

    builder = CrowdingIndexBuilder()
    crowding_indices = builder.build_all_crowding_indices(master_df)

    for name, df in crowding_indices.items():
        print(f"\n{name}: {df.shape}")
        if not df.empty:
            print(df.head())
