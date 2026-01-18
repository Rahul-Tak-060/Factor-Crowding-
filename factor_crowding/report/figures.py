"""Figure generation for research report."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from factor_crowding.config import data_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)

# Set publication-quality style
plt.style.use("seaborn-v0_8-paper")
sns.set_palette("husl")


class FigureGenerator:
    """Generate publication-quality figures for research report."""

    def __init__(self, output_dir: Path | None = None, dpi: int = 300):
        """Initialize the figure generator.

        Args:
            output_dir: Directory to save figures. Defaults to config.
            dpi: DPI for saved figures
        """
        self.output_dir = output_dir or data_config.figures_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi

    def save_figure(self, fig: plt.Figure, filename: str) -> None:
        """Save figure to output directory.

        Args:
            fig: Matplotlib figure
            filename: Filename (without path)
        """
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=self.dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {filepath}")

    def plot_crowding_index_timeseries(
        self,
        crowding_index: pd.Series,
        vix: pd.Series | None = None,
        stress_periods: list[tuple] | None = None,
        title: str = "Factor Crowding Index Over Time",
    ) -> plt.Figure:
        """Plot crowding index time series with optional stress periods.

        Args:
            crowding_index: Crowding index series
            vix: Optional VIX series to overlay
            stress_periods: Optional list of (start, end) tuples for stress periods
            title: Figure title

        Returns:
            Matplotlib figure
        """
        logger.info("Plotting crowding index time series...")

        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

        # Plot crowding index
        axes[0].plot(
            crowding_index.index, crowding_index.values, linewidth=1.5, label="Crowding Index"
        )
        axes[0].axhline(y=0, color="black", linestyle="--", alpha=0.3)

        # Shade stress periods if provided
        if stress_periods:
            for start, end in stress_periods:
                axes[0].axvspan(start, end, alpha=0.2, color="red", label="Stress Period")

        axes[0].set_ylabel("Crowding Index (Z-score)")
        axes[0].set_title(title)
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        # Plot VIX if provided
        if vix is not None:
            aligned_vix = vix.reindex(crowding_index.index)
            axes[1].plot(aligned_vix.index, aligned_vix.values, color="orange", linewidth=1.5)
            axes[1].set_ylabel("VIX")
            axes[1].set_xlabel("Date")
            axes[1].grid(alpha=0.3)
        else:
            fig.delaxes(axes[1])

        plt.tight_layout()
        self.save_figure(fig, "crowding_index_timeseries.png")

        return fig

    def plot_drawdown_comparison(
        self,
        drawdown_low: pd.Series,
        drawdown_high: pd.Series,
        labels: tuple[str, str] = ("Low Crowding", "High Crowding"),
        title: str = "Drawdown Comparison: Low vs High Crowding",
    ) -> plt.Figure:
        """Plot drawdown distributions for low vs high crowding periods.

        Args:
            drawdown_low: Drawdown series for low crowding
            drawdown_high: Drawdown series for high crowding
            labels: Labels for the two series
            title: Figure title

        Returns:
            Matplotlib figure
        """
        logger.info("Plotting drawdown comparison...")

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Time series
        axes[0].plot(drawdown_low.index, drawdown_low.values * 100, label=labels[0], alpha=0.7)
        axes[0].plot(drawdown_high.index, drawdown_high.values * 100, label=labels[1], alpha=0.7)
        axes[0].set_ylabel("Drawdown (%)")
        axes[0].set_xlabel("Date")
        axes[0].set_title("Drawdown Time Series")
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        # Distribution
        axes[1].hist(
            drawdown_low.dropna() * 100,
            bins=50,
            alpha=0.6,
            label=labels[0],
            density=True,
        )
        axes[1].hist(
            drawdown_high.dropna() * 100,
            bins=50,
            alpha=0.6,
            label=labels[1],
            density=True,
        )
        axes[1].set_xlabel("Drawdown (%)")
        axes[1].set_ylabel("Density")
        axes[1].set_title("Drawdown Distribution")
        axes[1].legend()
        axes[1].grid(alpha=0.3)

        plt.suptitle(title)
        plt.tight_layout()
        self.save_figure(fig, "drawdown_comparison.png")

        return fig

    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        title: str = "ROC Curve: Crash Prediction",
    ) -> plt.Figure:
        """Plot ROC curve for crash prediction model.

        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            title: Figure title

        Returns:
            Matplotlib figure
        """
        from sklearn.metrics import roc_auc_score, roc_curve

        logger.info("Plotting ROC curve...")

        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        auc = roc_auc_score(y_true, y_pred_proba)

        fig, ax = plt.subplots(figsize=(8, 8))

        ax.plot(fpr, tpr, linewidth=2, label=f"ROC Curve (AUC = {auc:.3f})")
        ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random Classifier")

        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title(title)
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)

        plt.tight_layout()
        self.save_figure(fig, "roc_curve.png")

        return fig

    def plot_conditional_returns(
        self,
        conditional_stats: pd.DataFrame,
        window: int,
        title_prefix: str = "Forward Returns by Crowding Decile",
    ) -> plt.Figure:
        """Plot forward returns conditional on crowding deciles.

        Args:
            conditional_stats: DataFrame with conditional statistics
            window: Forward window in days
            title_prefix: Prefix for figure title

        Returns:
            Matplotlib figure
        """
        logger.info(f"Plotting conditional returns (window={window})...")

        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract mean returns
        if isinstance(conditional_stats.columns, pd.MultiIndex):
            mean_returns = conditional_stats[("forward_return", "mean")]
        else:
            mean_returns = conditional_stats["mean"]

        deciles = range(len(mean_returns))
        ax.bar(deciles, mean_returns.values * 100, alpha=0.7)

        ax.set_xlabel("Crowding Decile (0=Low, 9=High)")
        ax.set_ylabel(f"{window}-Day Forward Return (%)")
        ax.set_title(f"{title_prefix} ({window}-Day Window)")
        ax.grid(alpha=0.3, axis="y")

        # Add horizontal line at zero
        ax.axhline(y=0, color="black", linestyle="--", linewidth=1)

        plt.tight_layout()
        self.save_figure(fig, f"conditional_returns_{window}d.png")

        return fig

    def plot_coefficient_analysis(
        self,
        coefficients: pd.Series,
        title: str = "Logistic Regression Coefficients",
    ) -> plt.Figure:
        """Plot model coefficients.

        Args:
            coefficients: Series of coefficients
            title: Figure title

        Returns:
            Matplotlib figure
        """
        logger.info("Plotting coefficient analysis...")

        fig, ax = plt.subplots(figsize=(10, 6))

        coefficients.sort_values().plot(kind="barh", ax=ax, alpha=0.7)

        ax.set_xlabel("Coefficient Value")
        ax.set_title(title)
        ax.axvline(x=0, color="black", linestyle="--", linewidth=1)
        ax.grid(alpha=0.3, axis="x")

        plt.tight_layout()
        self.save_figure(fig, "model_coefficients.png")

        return fig

    def plot_correlation_heatmap(
        self,
        correlation_matrix: pd.DataFrame,
        title: str = "Feature Correlation Heatmap",
    ) -> plt.Figure:
        """Plot correlation heatmap.

        Args:
            correlation_matrix: Correlation matrix
            title: Figure title

        Returns:
            Matplotlib figure
        """
        logger.info("Plotting correlation heatmap...")

        fig, ax = plt.subplots(figsize=(12, 10))

        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
            ax=ax,
        )

        ax.set_title(title)

        plt.tight_layout()
        self.save_figure(fig, "correlation_heatmap.png")

        return fig

    def plot_drawdown_episodes(
        self,
        episodes: pd.DataFrame,
        top_n: int = 10,
        title: str = "Top Drawdown Episodes",
    ) -> plt.Figure:
        """Plot top drawdown episodes.

        Args:
            episodes: DataFrame with drawdown episodes
            top_n: Number of top episodes to show
            title: Figure title

        Returns:
            Matplotlib figure
        """
        logger.info("Plotting drawdown episodes...")

        # Sort by depth and take top N
        top_episodes = episodes.nlargest(top_n, "depth_pct", keep="first")

        fig, ax = plt.subplots(figsize=(12, 6))

        labels = [f"{row['start_date'].strftime('%Y-%m-%d')}" for _, row in top_episodes.iterrows()]

        ax.barh(labels, top_episodes["depth_pct"].abs(), alpha=0.7)
        ax.set_xlabel("Drawdown Depth (%)")
        ax.set_title(title)
        ax.grid(alpha=0.3, axis="x")

        plt.tight_layout()
        self.save_figure(fig, "top_drawdown_episodes.png")

        return fig


if __name__ == "__main__":
    # Example usage
    from factor_crowding.analysis.drawdowns import DrawdownAnalyzer
    from factor_crowding.data.clean import DataCleaner
    from factor_crowding.features.crowding import CrowdingIndexBuilder

    # Load data
    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date="2010-01-01")

    # Build crowding index
    builder = CrowdingIndexBuilder()
    crowding_results = builder.build_all_crowding_indices(master_df)
    crowding_idx = crowding_results["crowding_index_all"]["CrowdingIndex_All"]

    # Generate figures
    fig_gen = FigureGenerator()
    fig_gen.plot_crowding_index_timeseries(crowding_idx, master_df["VIX"])

    # Drawdown analysis
    analyzer = DrawdownAnalyzer()
    drawdown = analyzer.compute_drawdown(master_df["Mom"])
    episodes = analyzer.compute_drawdown_episodes(master_df["Mom"])

    fig_gen.plot_drawdown_episodes(episodes)
