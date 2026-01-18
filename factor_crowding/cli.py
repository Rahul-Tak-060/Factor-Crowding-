"""Command-line interface for factor crowding analysis."""


import click
import pandas as pd

from factor_crowding.analysis.drawdowns import DrawdownAnalyzer
from factor_crowding.config import data_config
from factor_crowding.data.clean import DataCleaner
from factor_crowding.data.download import DataDownloader
from factor_crowding.features.crowding import CrowdingIndexBuilder
from factor_crowding.models.predict import CrashPredictor
from factor_crowding.report.figures import FigureGenerator
from factor_crowding.utils import setup_logger

logger = setup_logger("factor_crowding.cli")


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Factor Crowding and Crash Risk Analysis.

    A research pipeline for analyzing the relationship between factor crowding
    and drawdown risk in equity markets.
    """
    pass


@main.command()
@click.option(
    "--start",
    default="2010-01-01",
    help="Start date for data download (YYYY-MM-DD)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force re-download even if cached",
)
def download(start: str, force: bool) -> None:
    """Download all required data."""
    logger.info("Starting data download...")
    downloader = DataDownloader()
    downloader.download_all(start_date=start, force_refresh=force)
    logger.info("Download complete!")


@main.command()
@click.option(
    "--start",
    default="2010-01-01",
    help="Start date for analysis (YYYY-MM-DD)",
)
def clean(start: str) -> None:
    """Clean and align downloaded data."""
    logger.info("Starting data cleaning...")
    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date=start)
    logger.info(f"Master dataset created: {master_df.shape}")
    logger.info("Cleaning complete!")


@main.command()
@click.option(
    "--start",
    default="2010-01-01",
    help="Start date for analysis (YYYY-MM-DD)",
)
@click.option(
    "--end",
    default=None,
    help="End date for analysis (YYYY-MM-DD). Default: today",
)
@click.option(
    "--force-download",
    is_flag=True,
    help="Force re-download data",
)
def run(start: str, end: str | None, force_download: bool) -> None:
    """Run the complete analysis pipeline."""
    logger.info("=" * 80)
    logger.info("Starting Factor Crowding Analysis Pipeline")
    logger.info("=" * 80)

    # Step 1: Download data
    logger.info("\n[1/6] Downloading data...")
    downloader = DataDownloader()
    downloader.download_all(start_date=start, force_refresh=force_download)

    # Step 2: Clean and align data
    logger.info("\n[2/6] Cleaning and aligning data...")
    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date=start)

    if end:
        master_df = master_df[master_df.index <= end]

    logger.info(f"Master dataset: {master_df.shape}")
    logger.info(f"Date range: {master_df.index.min()} to {master_df.index.max()}")

    # Step 3: Build crowding indices
    logger.info("\n[3/6] Building crowding indices...")
    builder = CrowdingIndexBuilder()
    crowding_results = builder.build_all_crowding_indices(master_df)

    # Save crowding indices
    for name, df in crowding_results.items():
        if isinstance(df, pd.DataFrame):
            output_file = data_config.processed_data_dir / f"{name}.csv"
            df.to_csv(output_file)
            logger.info(f"Saved {name} to {output_file}")

    # Step 4: Analyze drawdowns
    logger.info("\n[4/6] Analyzing drawdowns and crash events...")
    analyzer = DrawdownAnalyzer()
    drawdown_results = analyzer.analyze_factor_drawdowns(master_df[["Mkt-RF", "SMB", "HML", "Mom"]])

    # Save drawdown analysis
    for factor, results in drawdown_results.items():
        output_file = data_config.processed_data_dir / f"drawdown_{factor}.csv"
        results["drawdown_series"].to_csv(output_file)

        episodes_file = data_config.processed_data_dir / f"episodes_{factor}.csv"
        results["episodes"].to_csv(episodes_file, index=False)

    # Step 5: Predictive modeling
    logger.info("\n[5/6] Running predictive models...")
    predictor = CrashPredictor()

    # Use composite crowding index
    if "crowding_index_all" in crowding_results:
        crowding_idx = crowding_results["crowding_index_all"]["CrowdingIndex_All"]
        mom_crashes = drawdown_results["Mom"]["daily_crashes"]

        # Prepare predictive dataset
        pred_data = predictor.prepare_predictive_dataset(
            master_df, crowding_idx, mom_crashes, forward_window=5
        )

        # Fit logistic model
        X = pred_data.drop(columns=["crash_target"])
        y = pred_data["crash_target"]

        if len(y.unique()) > 1:  # Check if we have both classes
            model_results = predictor.fit_logistic_model(X, y)

            # Save model results
            results_file = data_config.processed_data_dir / "model_results.txt"
            with open(results_file, "w") as f:
                f.write("Logistic Regression Results\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Train AUC: {model_results['train_auc']:.4f}\n")
                f.write(f"Test AUC: {model_results['test_auc']:.4f}\n\n")
                f.write("Coefficients:\n")
                f.write(str(model_results["coefficients"]))

            # Forward return analysis
            forward_results = predictor.forward_return_analysis(
                master_df, crowding_idx, return_col="Mom"
            )
        else:
            logger.warning("Insufficient crash events for modeling")
            model_results = None
            forward_results = None
    else:
        logger.warning("No composite crowding index found")
        model_results = None
        forward_results = None

    # Step 6: Generate figures
    logger.info("\n[6/6] Generating figures...")
    fig_gen = FigureGenerator()

    # Crowding index time series
    if "crowding_index_all" in crowding_results:
        fig_gen.plot_crowding_index_timeseries(
            crowding_results["crowding_index_all"]["CrowdingIndex_All"],
            master_df["VIX"],
        )

    # Drawdown episodes
    if "Mom" in drawdown_results:
        fig_gen.plot_drawdown_episodes(drawdown_results["Mom"]["episodes"])

    # ROC curve
    if model_results:
        fig_gen.plot_roc_curve(
            model_results["y_test"],
            model_results["y_pred_proba_test"],
        )

        # Coefficient plot
        fig_gen.plot_coefficient_analysis(model_results["coefficients"])

    # Conditional returns
    if forward_results:
        for window, stats in forward_results.items():
            fig_gen.plot_conditional_returns(stats, window)

    # Correlation heatmap
    if "crowding_index_all" in crowding_results:
        corr_data = crowding_results["crowding_index_all"].join(master_df[["VIX", "Mom", "Mkt-RF"]])
        fig_gen.plot_correlation_heatmap(corr_data.corr())

    logger.info("\n" + "=" * 80)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Outputs saved to: {data_config.output_dir}")
    logger.info("=" * 80)


@main.command()
def info() -> None:
    """Display project configuration information."""
    click.echo("\nFactor Crowding Analysis - Configuration")
    click.echo("=" * 50)
    click.echo(f"\nData Directory: {data_config.data_dir}")
    click.echo(f"Raw Data: {data_config.raw_data_dir}")
    click.echo(f"Processed Data: {data_config.processed_data_dir}")
    click.echo(f"Outputs: {data_config.output_dir}")
    click.echo(f"Figures: {data_config.figures_dir}")
    click.echo(f"\nETF Tickers: {', '.join(data_config.etf_tickers)}")
    click.echo(f"Fama-French Factors: {', '.join(data_config.ff_factors)}")
    click.echo(f"VIX Series: {data_config.vix_series}")
    click.echo()


if __name__ == "__main__":
    main()
