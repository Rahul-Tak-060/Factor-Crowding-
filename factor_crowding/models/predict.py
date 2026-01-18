"""Predictive modeling for crash risk using crowding indices."""

from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from statsmodels.regression.quantile_regression import QuantReg

from factor_crowding.config import analysis_config
from factor_crowding.utils import setup_logger

logger = setup_logger(__name__)


class CrashPredictor:
    """Predict crash events using crowding indices and market stress."""

    def __init__(self, random_state: int = analysis_config.random_seed):
        """Initialize the crash predictor.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.models: dict[str, Any] = {}
        self.results: dict[str, Any] = {}

    def prepare_predictive_dataset(
        self,
        master_data: pd.DataFrame,
        crowding_index: pd.Series,
        crash_flags: pd.Series,
        vix_col: str = "VIX",
        forward_window: int = 5,
    ) -> pd.DataFrame:
        """Prepare dataset for predictive modeling.

        Args:
            master_data: Master dataset with all features
            crowding_index: Crowding index series
            crash_flags: Boolean series of crash events
            vix_col: Name of VIX column
            forward_window: Days forward to predict crash

        Returns:
            DataFrame with features and target aligned
        """
        logger.info(f"Preparing predictive dataset (forward_window={forward_window})...")

        # Align crowding index with master data
        df = pd.DataFrame(index=master_data.index)
        df["crowding_index"] = crowding_index

        # Add VIX
        if vix_col in master_data.columns:
            df["vix"] = master_data[vix_col]

            # VIX stress regime
            vix_75 = master_data[vix_col].rolling(252).quantile(0.75)
            vix_25 = master_data[vix_col].rolling(252).quantile(0.25)

            df["vix_high_stress"] = (master_data[vix_col] > vix_75).astype(int)
            df["vix_low_stress"] = (master_data[vix_col] < vix_25).astype(int)
        else:
            logger.warning(f"VIX column '{vix_col}' not found")

        # Add recent volatility (control variable)
        if "Mom" in master_data.columns:
            df["mom_vol_20d"] = master_data["Mom"].rolling(20).std()
            df["mom_ret_20d"] = master_data["Mom"].rolling(20).sum()

        # Add market return (control)
        if "Mkt-RF" in master_data.columns:
            df["mkt_ret_20d"] = master_data["Mkt-RF"].rolling(20).sum()

        # Forward crash target
        df["crash_target"] = crash_flags.shift(-forward_window).fillna(0).astype(int)

        # Interaction term: crowding * high stress
        if "vix_high_stress" in df.columns:
            df["crowding_x_stress"] = df["crowding_index"] * df["vix_high_stress"]

        # Drop NaNs
        initial_len = len(df)
        df = df.dropna()
        logger.info(f"Dataset prepared: {len(df)} observations ({initial_len - len(df)} dropped)")

        return df

    def fit_logistic_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fit logistic regression model to predict crashes.

        Args:
            X: Feature DataFrame
            y: Target series (crash flags)
            test_size: Proportion of data for testing
            features: List of feature names to use. Uses all if None.

        Returns:
            Dictionary with model, predictions, and metrics
        """
        logger.info("Fitting logistic regression model...")

        if features is None:
            features = [col for col in X.columns if col != "crash_target"]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X[features],
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y if y.nunique() > 1 else None,
        )

        # Fit model
        model = LogisticRegression(
            random_state=self.random_state,
            max_iter=1000,
            class_weight="balanced",
        )
        model.fit(X_train, y_train)

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        y_pred_proba_train = model.predict_proba(X_train)[:, 1]
        y_pred_proba_test = model.predict_proba(X_test)[:, 1]

        # Metrics
        train_auc = roc_auc_score(y_train, y_pred_proba_train)
        test_auc = roc_auc_score(y_test, y_pred_proba_test)

        logger.info(f"Train AUC: {train_auc:.4f}, Test AUC: {test_auc:.4f}")

        # Store results
        results = {
            "model": model,
            "features": features,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "y_pred_train": y_pred_train,
            "y_pred_test": y_pred_test,
            "y_pred_proba_train": y_pred_proba_train,
            "y_pred_proba_test": y_pred_proba_test,
            "train_auc": train_auc,
            "test_auc": test_auc,
            "coefficients": pd.Series(model.coef_[0], index=features),
            "intercept": model.intercept_[0],
        }

        # Classification report
        logger.info("\nTest set classification report:")
        report = classification_report(y_test, y_pred_test)
        logger.info(f"\n{report}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred_test)
        logger.info(f"\nConfusion matrix:\n{cm}")

        return results

    def fit_quantile_regression(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        quantile: float = 0.05,
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fit quantile regression to model tail risk.

        Args:
            X: Feature DataFrame
            y: Target series (forward returns)
            quantile: Quantile to model (e.g., 0.05 for 5th percentile)
            features: List of feature names to use

        Returns:
            Dictionary with model and results
        """
        logger.info(f"Fitting quantile regression (q={quantile})...")

        if features is None:
            features = [col for col in X.columns if col not in ["crash_target"]]

        # Prepare data
        X_use = X[features].copy()
        X_use = X_use.join(y.rename("target"))
        X_use = X_use.dropna()

        # Fit quantile regression
        model = QuantReg(X_use["target"], X_use[features])
        result = model.fit(q=quantile)

        logger.info(f"\nQuantile regression summary:\n{result.summary()}")

        return {
            "model": model,
            "result": result,
            "quantile": quantile,
            "features": features,
            "coefficients": result.params,
        }

    def conditional_analysis(
        self,
        data: pd.DataFrame,
        crowding_col: str = "crowding_index",
        target_col: str = "crash_target",
        n_bins: int = 10,
    ) -> pd.DataFrame:
        """Analyze target variable conditional on crowding deciles.

        Args:
            data: DataFrame with crowding and target
            crowding_col: Name of crowding index column
            target_col: Name of target column
            n_bins: Number of bins for crowding

        Returns:
            DataFrame with conditional statistics by bin
        """
        logger.info(f"Performing conditional analysis ({n_bins} bins)...")

        # Create bins
        data = data.copy()
        data["crowding_bin"] = pd.qcut(
            data[crowding_col],
            q=n_bins,
            labels=False,
            duplicates="drop",
        )

        # Compute statistics by bin
        conditional_stats = (
            data.groupby("crowding_bin")
            .agg(
                {
                    target_col: ["count", "mean", "std"],
                    crowding_col: ["mean", "min", "max"],
                }
            )
            .round(4)
        )

        logger.info(f"\nConditional statistics:\n{conditional_stats}")

        return conditional_stats

    def forward_return_analysis(
        self,
        master_data: pd.DataFrame,
        crowding_index: pd.Series,
        return_col: str = "Mom",
        forward_windows: list[int] | None = None,
        n_bins: int = 10,
    ) -> dict[int, pd.DataFrame]:
        """Analyze forward returns conditional on crowding.

        Args:
            master_data: Master dataset
            crowding_index: Crowding index series
            return_col: Column name for returns
            forward_windows: List of forward windows (e.g., [5, 20])
            n_bins: Number of crowding bins

        Returns:
            Dictionary mapping window to conditional statistics
        """
        if forward_windows is None:
            forward_windows = analysis_config.forward_windows

        logger.info(f"Analyzing forward returns for windows: {forward_windows}")

        results = {}
        for window in forward_windows:
            # Compute forward returns
            forward_ret = master_data[return_col].rolling(window).sum().shift(-window)

            # Create analysis dataset
            analysis_df = pd.DataFrame(
                {
                    "crowding_index": crowding_index,
                    "forward_return": forward_ret,
                }
            ).dropna()

            # Conditional analysis
            stats = self.conditional_analysis(
                analysis_df,
                crowding_col="crowding_index",
                target_col="forward_return",
                n_bins=n_bins,
            )

            results[window] = stats

        return results


if __name__ == "__main__":
    # Example usage
    from factor_crowding.analysis.drawdowns import DrawdownAnalyzer
    from factor_crowding.data.clean import DataCleaner
    from factor_crowding.features.crowding import CrowdingIndexBuilder

    # Load and prepare data
    cleaner = DataCleaner()
    master_df = cleaner.create_master_dataset(start_date="2010-01-01")

    # Build crowding index
    builder = CrowdingIndexBuilder()
    crowding_results = builder.build_all_crowding_indices(master_df)
    crowding_idx = crowding_results["crowding_index_all"]["CrowdingIndex_All"]

    # Identify crashes
    analyzer = DrawdownAnalyzer()
    crashes = analyzer.identify_crash_events(master_df["Mom"], window=1)

    # Prepare predictive dataset
    predictor = CrashPredictor()
    pred_data = predictor.prepare_predictive_dataset(
        master_df, crowding_idx, crashes, forward_window=5
    )

    # Fit logistic model
    X = pred_data.drop(columns=["crash_target"])
    y = pred_data["crash_target"]
    results = predictor.fit_logistic_model(X, y)

    print(f"\nFeature coefficients:\n{results['coefficients']}")
