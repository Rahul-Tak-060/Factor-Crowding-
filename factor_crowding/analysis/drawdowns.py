"""Drawdown computation and crash event identification."""


import pandas as pd

from factor_crowding.config import analysis_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)


class DrawdownAnalyzer:
    """Analyze drawdowns and identify crash events in return series."""

    def __init__(
        self,
        crash_percentile: float = analysis_config.crash_percentile,
        drawdown_threshold: float = analysis_config.drawdown_threshold_pct,
    ):
        """Initialize the drawdown analyzer.

        Args:
            crash_percentile: Percentile threshold for crash definition
            drawdown_threshold: Drawdown percentage threshold for episode detection
        """
        self.crash_percentile = crash_percentile
        self.drawdown_threshold = drawdown_threshold

    def compute_cumulative_returns(self, returns: pd.Series) -> pd.Series:
        """Compute cumulative returns from a return series.

        Args:
            returns: Series of returns

        Returns:
            Series of cumulative returns (wealth index)
        """
        return (1 + returns).cumprod()

    def compute_running_max(self, cumulative_returns: pd.Series) -> pd.Series:
        """Compute running maximum of cumulative returns.

        Args:
            cumulative_returns: Series of cumulative returns

        Returns:
            Series of running maximum values
        """
        return cumulative_returns.expanding().max()

    def compute_drawdown(self, returns: pd.Series) -> pd.Series:
        """Compute drawdown series from returns.

        Args:
            returns: Series of returns

        Returns:
            Series of drawdowns (as decimals, e.g., -0.05 for 5% drawdown)
        """
        cum_returns = self.compute_cumulative_returns(returns)
        running_max = self.compute_running_max(cum_returns)
        drawdown = (cum_returns - running_max) / running_max
        return drawdown

    def identify_crash_events(
        self,
        returns: pd.Series,
        window: int = 1,
        method: str = "historical",
    ) -> pd.Series:
        """Identify crash events based on extreme negative returns.

        Args:
            returns: Series of returns
            window: Window for computing multi-day returns (1 for daily)
            method: 'historical' uses percentile of entire history,
                   'rolling' uses rolling percentile

        Returns:
            Boolean series indicating crash events
        """
        logger.info(f"Identifying crash events (window={window}, method={method})...")

        # Compute returns over specified window
        if window == 1:
            period_returns = returns
        else:
            period_returns = (1 + returns).rolling(window).apply(lambda x: x.prod() - 1, raw=True)

        # Determine crash threshold
        if method == "historical":
            threshold = period_returns.quantile(self.crash_percentile / 100)
            crashes = period_returns < threshold
        elif method == "rolling":
            # Use expanding window to avoid look-ahead bias
            rolling_threshold = period_returns.expanding().quantile(self.crash_percentile / 100)
            crashes = period_returns < rolling_threshold
        else:
            raise ValueError(f"Unknown method: {method}")

        num_crashes = crashes.sum()
        logger.info(f"Identified {num_crashes} crash events ({num_crashes/len(crashes)*100:.2f}%)")

        return crashes

    def compute_drawdown_episodes(self, returns: pd.Series) -> pd.DataFrame:
        """Identify discrete drawdown episodes.

        Args:
            returns: Series of returns

        Returns:
            DataFrame with drawdown episodes (start, trough, end, depth, duration)
        """
        logger.info("Computing drawdown episodes...")

        drawdown = self.compute_drawdown(returns)
        cum_returns = self.compute_cumulative_returns(returns)

        # Identify when we're in a drawdown
        in_drawdown = drawdown < 0

        # Find start and end points of drawdown episodes
        episodes = []
        start_idx = None

        for i in range(len(in_drawdown)):
            if in_drawdown.iloc[i] and start_idx is None:
                # Start of new drawdown
                start_idx = i
            elif not in_drawdown.iloc[i] and start_idx is not None:
                # End of drawdown
                end_idx = i - 1

                # Find trough (maximum drawdown point)
                episode_dd = drawdown.iloc[start_idx : end_idx + 1]
                trough_idx = start_idx + episode_dd.argmin()

                # Compute metrics
                depth = drawdown.iloc[trough_idx]
                duration = end_idx - start_idx + 1

                # Only record if exceeds threshold
                if abs(depth) >= self.drawdown_threshold / 100:
                    episodes.append(
                        {
                            "start_date": drawdown.index[start_idx],
                            "trough_date": drawdown.index[trough_idx],
                            "end_date": drawdown.index[end_idx],
                            "depth_pct": depth * 100,
                            "duration_days": duration,
                            "start_value": cum_returns.iloc[start_idx],
                            "trough_value": cum_returns.iloc[trough_idx],
                        }
                    )

                start_idx = None

        # Handle case where drawdown continues to end of series
        if start_idx is not None:
            episode_dd = drawdown.iloc[start_idx:]
            trough_idx = start_idx + episode_dd.argmin()
            depth = drawdown.iloc[trough_idx]
            duration = len(drawdown) - start_idx

            if abs(depth) >= self.drawdown_threshold / 100:
                episodes.append(
                    {
                        "start_date": drawdown.index[start_idx],
                        "trough_date": drawdown.index[trough_idx],
                        "end_date": drawdown.index[-1],
                        "depth_pct": depth * 100,
                        "duration_days": duration,
                        "start_value": cum_returns.iloc[start_idx],
                        "trough_value": cum_returns.iloc[trough_idx],
                    }
                )

        episodes_df = pd.DataFrame(episodes)
        logger.info(f"Identified {len(episodes_df)} drawdown episodes")

        return episodes_df

    def compute_max_drawdown(self, returns: pd.Series) -> float:
        """Compute maximum drawdown.

        Args:
            returns: Series of returns

        Returns:
            Maximum drawdown as a decimal (e.g., -0.25 for 25% drawdown)
        """
        drawdown = self.compute_drawdown(returns)
        return drawdown.min()

    def analyze_factor_drawdowns(self, factor_returns: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Analyze drawdowns for multiple factors.

        Args:
            factor_returns: DataFrame with factor returns

        Returns:
            Dictionary mapping factor name to drawdown analysis
        """
        logger.info("Analyzing drawdowns for all factors...")

        results = {}
        for factor in factor_returns.columns:
            logger.info(f"Analyzing {factor}...")

            # Compute drawdown series
            dd_series = self.compute_drawdown(factor_returns[factor])

            # Identify crash events (daily and weekly)
            daily_crashes = self.identify_crash_events(factor_returns[factor], window=1)
            weekly_crashes = self.identify_crash_events(factor_returns[factor], window=5)

            # Compute episodes
            episodes = self.compute_drawdown_episodes(factor_returns[factor])

            # Store results
            results[factor] = {
                "drawdown_series": dd_series,
                "daily_crashes": daily_crashes,
                "weekly_crashes": weekly_crashes,
                "episodes": episodes,
                "max_drawdown": self.compute_max_drawdown(factor_returns[factor]),
            }

        return results


if __name__ == "__main__":
    # Example usage
    from factor_crowding.data.clean import DataCleaner

    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date="2010-01-01")

    # Analyze Momentum factor
    analyzer = DrawdownAnalyzer()
    mom_returns = master_df["Mom"]

    drawdown = analyzer.compute_drawdown(mom_returns)
    print(f"Max drawdown: {analyzer.compute_max_drawdown(mom_returns):.2%}")

    episodes = analyzer.compute_drawdown_episodes(mom_returns)
    print(f"\nDrawdown episodes:\n{episodes}")

    daily_crashes = analyzer.identify_crash_events(mom_returns, window=1)
    print(f"\nDaily crashes: {daily_crashes.sum()}")
