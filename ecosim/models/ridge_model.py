"""Ridge Regression Forecasting Engine for EcoSim.

Strictly adheres to project requirements:
- Only machine-learning model used is Ridge Regression (sklearn.linear_model.Ridge).
- Strict chronological holdout splits without random shuffling to prevent time-series leakage.
- Scaler fit solely on training partition.
- Computes empirical evaluation metrics: MAE, RMSE, and out-of-sample R-squared.
- Provides deep econometric interpretability and reliability diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURE_METADATA = {
    "gdp_growth_yoy": {
        "name": "Real GDP Growth (YoY %)",
        "role": "Aggregate Demand & Capacity Strain",
        "description": "Measures real economic expansion. Positive growth above potential strains productive capacity, creating demand-pull price pressures.",
    },
    "inflation_yoy": {
        "name": "Observed CPI Inflation (YoY %)",
        "role": "Inflation Persistence & Inertia",
        "description": "Reflects backward-looking inflation inertia, staggered pricing contracts, and adaptive household/business expectations.",
    },
    "UNRATE": {
        "name": "Civilian Unemployment Rate (%)",
        "role": "Labor Market Slack (Phillips Channel)",
        "description": "Measures labor market slack. Low unemployment tightens labor supply, inducing upward wage-push cost pressures on final consumer prices.",
    },
    "FEDFUNDS": {
        "name": "Effective Federal Funds Rate (%)",
        "role": "Monetary Policy Stance",
        "description": "Measures nominal policy stance. Higher policy rates tighten borrowing conditions, curbing credit growth and cooling aggregate demand.",
    },
}


@dataclass
class RidgeEvaluationResults:
    """Evaluation metrics, diagnostic artifacts, and predictions for chronological test split."""

    mae: float
    rmse: float
    r2: float
    train_size: int
    test_size: int
    split_date: pd.Timestamp
    train_date_range: tuple[pd.Timestamp, pd.Timestamp]
    test_date_range: tuple[pd.Timestamp, pd.Timestamp]
    train_quarter_labels: tuple[str, str]
    test_quarter_labels: tuple[str, str]
    df_train_actual_pred: pd.DataFrame
    df_test_actual_pred: pd.DataFrame
    coefficients: pd.DataFrame
    intercept: float
    alpha: float
    next_unseen_forecast: float | None
    next_forecast_date: pd.Timestamp | None
    next_forecast_label: str | None
    latest_feature_values: dict[str, float]
    is_reliable: bool
    reliability_notes: list[str]


class MacroRidgeForecaster:
    """Ridge Regression model dedicated exclusively to next-quarter inflation prediction."""

    def __init__(self, alpha: float = 1.0):
        """Initialize Ridge Forecaster.

        Args:
            alpha: L2 regularization strength. Larger values enforce heavier shrinkage.
        """
        self.alpha = float(alpha)
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=self.alpha)
        self.is_trained = False
        self.feature_names: list[str] = []

    def train_and_evaluate(
        self,
        clean_df: pd.DataFrame,
        feature_cols: list[str],
        target_col: str,
        test_ratio: float = 0.20,
    ) -> RidgeEvaluationResults:
        """Train model on chronological training window and evaluate on out-of-sample test window.

        Args:
            clean_df: Chronologically sorted DataFrame containing features and target.
            feature_cols: List of feature names (observed at or before time t).
            target_col: Target column name (inflation at t+1).
            test_ratio: Proportion of recent observations reserved for holdout testing (e.g. 0.20).

        Returns:
            RidgeEvaluationResults containing metrics, coefficient table, and prediction series.
        """
        self.feature_names = feature_cols

        # Separate the very last row if target is NaN (which represents current period waiting for next quarter)
        model_ready = clean_df.dropna(subset=[target_col]).copy()
        unseen_row = clean_df[clean_df[target_col].isna()].copy()

        n_samples = len(model_ready)
        if n_samples < 24:
            raise ValueError(
                f"Insufficient historical samples to calibrate Ridge model: {n_samples} valid quarters "
                f"available (minimum 24 quarters required for stable estimation and chronological testing)."
            )

        # Chronological Split (NEVER randomly shuffle)
        split_idx = int(n_samples * (1.0 - test_ratio))
        split_idx = max(16, min(split_idx, n_samples - 4))  # Ensure both train and test have sufficient size

        train_df = model_ready.iloc[:split_idx].copy()
        test_df = model_ready.iloc[split_idx:].copy()

        split_date = test_df["date"].iloc[0]
        train_date_range = (train_df["date"].iloc[0], train_df["date"].iloc[-1])
        test_date_range = (test_df["date"].iloc[0], test_df["date"].iloc[-1])

        # Extract quarter labels
        def get_q_lbl(row: pd.Series) -> str:
            if "quarter_label" in row and pd.notna(row["quarter_label"]):
                return str(row["quarter_label"])
            dt = row["date"]
            q = ((dt.month - 1) // 3) + 1
            return f"Q{q} {dt.year}"

        train_quarter_labels = (get_q_lbl(train_df.iloc[0]), get_q_lbl(train_df.iloc[-1]))
        test_quarter_labels = (get_q_lbl(test_df.iloc[0]), get_q_lbl(test_df.iloc[-1]))

        X_train_raw = train_df[feature_cols].values
        y_train = train_df[target_col].values

        X_test_raw = test_df[feature_cols].values
        y_test = test_df[target_col].values

        # Scale features: Fit strictly on training partition to eliminate lookahead leakage
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_test_scaled = self.scaler.transform(X_test_raw)

        # Fit Ridge Regression
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        # In-sample predictions
        y_train_pred = self.model.predict(X_train_scaled)
        train_df["actual"] = y_train
        train_df["predicted"] = y_train_pred

        # Out-of-sample holdout predictions
        y_test_pred = self.model.predict(X_test_scaled)
        test_df["actual"] = y_test
        test_df["predicted"] = y_test_pred

        # Metrics on chronological test set
        mae = float(mean_absolute_error(y_test, y_test_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_test_pred)))
        r2 = float(r2_score(y_test, y_test_pred))

        # Standardized coefficients table with economic descriptions
        coef_records = []
        for feat, coef in zip(feature_cols, self.model.coef_):
            meta = FEATURE_METADATA.get(feat, {"name": feat, "role": "Macro Predictor", "description": ""})
            coef_records.append({
                "Feature": feat,
                "Feature_Name": meta["name"],
                "Economic_Role": meta["role"],
                "Standardized_Coefficient": float(coef),
                "Absolute_Weight": float(abs(coef)),
                "Impact_Direction": "Upward pressure (+)" if coef > 0 else "Downward pressure (-)",
                "Description": meta["description"],
            })

        coef_df = pd.DataFrame(coef_records).sort_values("Absolute_Weight", ascending=False).reset_index(drop=True)

        # Forecast next unseen period if latest observation is available
        next_forecast = None
        next_date = None
        next_label = None
        latest_feature_vals: dict[str, float] = {}

        if not unseen_row.empty:
            latest_row = unseen_row.iloc[-1]
            for f in feature_cols:
                latest_feature_vals[f] = float(latest_row[f]) if pd.notna(latest_row[f]) else 0.0

            latest_x_raw = unseen_row[feature_cols].values
            latest_x_scaled = self.scaler.transform(latest_x_raw)
            next_forecast = float(self.model.predict(latest_x_scaled)[0])
            latest_obs_date = unseen_row["date"].iloc[-1]
            next_date = latest_obs_date + pd.DateOffset(months=3)
            q_num = ((next_date.month - 1) // 3) + 1
            next_label = f"Q{q_num} {next_date.year}"

        # Reliability diagnostics
        reliability_notes: list[str] = []
        is_reliable = True

        if len(test_df) < 12:
            reliability_notes.append(
                f"Holdout evaluation sample is small ({len(test_df)} quarters). Metrics reflect limited historical coverage."
            )
        if r2 < 0:
            is_reliable = False
            reliability_notes.append(
                f"Out-of-sample R² is negative ({r2:.3f}), indicating the model underperformed a simple historical mean "
                "baseline on the holdout period. This commonly occurs across structural regime breaks (e.g. COVID-19 pandemic supply shocks)."
            )
        elif r2 < 0.25:
            reliability_notes.append(
                f"Modest out-of-sample explanatory power (R² = {r2:.3f}). Macroeconomic inflation is influenced by unmodeled global supply shocks."
            )

        if mae > 2.5:
            reliability_notes.append(
                f"Holdout Mean Absolute Error ({mae:.2f}%) indicates wide error margins during volatile historical intervals."
            )

        return RidgeEvaluationResults(
            mae=mae,
            rmse=rmse,
            r2=r2,
            train_size=len(train_df),
            test_size=len(test_df),
            split_date=split_date,
            train_date_range=train_date_range,
            test_date_range=test_date_range,
            train_quarter_labels=train_quarter_labels,
            test_quarter_labels=test_quarter_labels,
            df_train_actual_pred=train_df,
            df_test_actual_pred=test_df,
            coefficients=coef_df,
            intercept=float(self.model.intercept_),
            alpha=self.alpha,
            next_unseen_forecast=next_forecast,
            next_forecast_date=next_date,
            next_forecast_label=next_label,
            latest_feature_values=latest_feature_vals,
            is_reliable=is_reliable,
            reliability_notes=reliability_notes,
        )
