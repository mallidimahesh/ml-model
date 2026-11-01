"""Phillips Curve & Ridge Regression Forecasting Engine for EcoSim.
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.data_service import data_service
from backend.config import SUPPORTED_COUNTRIES

logger = logging.getLogger(__name__)

FEATURE_METADATA = {
    "inflation_lag": {
        "name": "Lagged CPI Inflation (π_t)",
        "role": "Inflation Inertia & Staggered Pricing",
        "description": "Reflects backward-looking inertia, cost-of-living indexation contracts, and adaptive consumer expectations.",
    },
    "unemployment": {
        "name": "Civilian Unemployment Rate (u_t)",
        "role": "Labor Market Slack (Phillips Curve Channel)",
        "description": "Empirical Phillips Curve trade-off. Tighter labor markets (lower unemployment) generate upward wage pressure on consumer prices.",
    },
    "gdp_growth": {
        "name": "Real GDP Growth YoY (%_t)",
        "role": "Aggregate Demand & Capacity Strain",
        "description": "Measures demand-pull price pressures. Rapid real output expansion strains industrial capacity and supply chains.",
    },
    "interest_rate": {
        "name": "Policy Interest Rate (i_t)",
        "role": "Monetary Policy Stance",
        "description": "Borrowing costs set by the central bank. Higher interest rates dampen credit expansion and cool consumer aggregate demand.",
    },
}


class ModelsService:
    """Forecasting and econometric analysis service."""

    def run_ridge_forecast(
        self,
        country_code: str = "USA",
        alpha: float = 1.0,
        test_ratio: float = 0.20,
        selected_features: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute regularized Ridge regression for inflation forecasting."""
        country_code = country_code.upper()
        country_meta = SUPPORTED_COUNTRIES.get(country_code, {"name": country_code, "flag": "🌐"})

        if selected_features is None or len(selected_features) == 0:
            selected_features = ["inflation_lag", "unemployment", "gdp_growth", "interest_rate"]

        alpha = max(0.001, min(float(alpha), 100.0))
        test_ratio = max(0.10, min(float(test_ratio), 0.40))

        # Check frequency support
        if country_code == "USA":
            return self._forecast_usa_quarterly(alpha, test_ratio, selected_features)
        else:
            return self._forecast_annual_country(country_code, alpha, test_ratio, selected_features)

    def _forecast_usa_quarterly(
        self, alpha: float, test_ratio: float, features: list[str]
    ) -> dict[str, Any]:
        """Quarterly inflation forecasting using high-frequency FRED series."""
        gdp_df, _, _ = data_service.fetch_fred_series("GDPC1")
        cpi_df, _, _ = data_service.fetch_fred_series("CPIAUCSL")
        unrate_df, _, _ = data_service.fetch_fred_series("UNRATE")
        fed_df, _, _ = data_service.fetch_fred_series("FEDFUNDS")

        from ecosim.data.data_processor import harmonize_macro_series
        raw_dict = {
            "GDPC1": gdp_df,
            "CPIAUCSL": cpi_df,
            "UNRATE": unrate_df,
            "FEDFUNDS": fed_df,
        }
        monthly_df = harmonize_macro_series(raw_dict)
        if monthly_df.empty:
            raise ValueError("Insufficient FRED observations to construct quarterly dataset.")

        # Aggregate to quarterly
        monthly_df["quarter_period"] = pd.to_datetime(monthly_df["date"]).dt.to_period("Q")
        q_agg = monthly_df.groupby("quarter_period").agg({
            "date": "last",
            "GDPC1": "last",
            "CPIAUCSL": "mean",
            "UNRATE": "mean",
            "FEDFUNDS": "mean",
        }).reset_index()

        # YoY rates
        q_agg["gdp_growth"] = ((q_agg["GDPC1"] - q_agg["GDPC1"].shift(4)) / q_agg["GDPC1"].shift(4)) * 100
        q_agg["inflation_lag"] = ((q_agg["CPIAUCSL"] - q_agg["CPIAUCSL"].shift(4)) / q_agg["CPIAUCSL"].shift(4)) * 100
        q_agg["unemployment"] = q_agg["UNRATE"]
        q_agg["interest_rate"] = q_agg["FEDFUNDS"]

        # Target: Inflation in next quarter (t+1)
        q_agg["target"] = q_agg["inflation_lag"].shift(-1)
        q_agg["quarter_label"] = q_agg["quarter_period"].apply(lambda p: f"Q{p.quarter} {p.year}")
        q_agg["date_str"] = pd.to_datetime(q_agg["date"]).dt.strftime("%Y-%m-%d")

        # Clean valid training data
        available_features = [f for f in features if f in q_agg.columns]
        clean_df = q_agg.dropna(subset=available_features).copy().reset_index(drop=True)

        # Separate unseen latest row (where target is NaN because next quarter hasn't happened yet)
        model_ready = clean_df.dropna(subset=["target"]).copy().reset_index(drop=True)
        unseen_row = clean_df[clean_df["target"].isna()].copy()

        n_samples = len(model_ready)
        if n_samples < 24:
            raise ValueError(f"Insufficient quarterly samples ({n_samples} < 24 required).")

        # Chronological split (NEVER random shuffle)
        split_idx = int(n_samples * (1.0 - test_ratio))
        split_idx = max(16, min(split_idx, n_samples - 4))

        train_df = model_ready.iloc[:split_idx].copy()
        test_df = model_ready.iloc[split_idx:].copy()

        X_train_raw = train_df[available_features].values
        y_train = train_df["target"].values
        X_test_raw = test_df[available_features].values
        y_test = test_df["target"].values

        # Scaler fit STRICTLY on train partition to prevent lookahead leakage
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_raw)
        X_test_scaled = scaler.transform(X_test_raw)

        # Fit Ridge Regression
        model = Ridge(alpha=alpha)
        model.fit(X_train_scaled, y_train)

        # Predictions
        train_preds = model.predict(X_train_scaled)
        test_preds = model.predict(X_test_scaled)

        # Metrics on out-of-sample test partition
        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_r2 = float(r2_score(y_test, test_preds))

        train_mae = float(mean_absolute_error(y_train, train_preds))
        train_rmse = float(np.sqrt(mean_squared_error(y_train, train_preds)))

        # Naive Persistence Baseline: predict next period = current period inflation
        # (Target is y_{t+1}, persistence forecast is inflation_lag_t)
        baseline_preds = test_df["inflation_lag"].values
        base_mae = float(mean_absolute_error(y_test, baseline_preds))
        base_rmse = float(np.sqrt(mean_squared_error(y_test, baseline_preds)))

        # Outperformance check
        beats_baseline = test_rmse <= base_rmse

        # Standardized coefficients
        coef_records = []
        for feat, coef in zip(available_features, model.coef_):
            meta = FEATURE_METADATA.get(feat, {"name": feat, "role": "Macro Predictor", "description": ""})
            coef_records.append({
                "feature": feat,
                "name": meta["name"],
                "role": meta["role"],
                "coefficient": round(float(coef), 4),
                "abs_weight": round(float(abs(coef)), 4),
                "direction": "Upward pressure (+)" if coef > 0 else "Downward pressure (-)",
                "description": meta["description"],
            })
        coef_records = sorted(coef_records, key=lambda x: x["abs_weight"], reverse=True)

        # Next Quarter Unseen Forecast
        next_forecast = None
        next_label = None
        next_interval_low = None
        next_interval_high = None

        if not unseen_row.empty:
            latest_feat_vals = unseen_row[available_features].values[-1:]
            latest_scaled = scaler.transform(latest_feat_vals)
            next_forecast = round(float(model.predict(latest_scaled)[0]), 2)
            last_date = pd.to_datetime(unseen_row["date"].iloc[-1])
            target_date = last_date + pd.DateOffset(months=3)
            q_num = ((target_date.month - 1) // 3) + 1
            next_label = f"Q{q_num} {target_date.year}"
            next_interval_low = round(next_forecast - 1.96 * test_rmse, 2)
            next_interval_high = round(next_forecast + 1.96 * test_rmse, 2)

        # Actual vs Predicted time-series for chart
        chart_points = []
        for i, row in train_df.iterrows():
            chart_points.append({
                "date": row["date_str"],
                "label": row["quarter_label"],
                "split": "train",
                "actual": round(float(row["target"]), 2),
                "predicted": round(float(train_preds[train_df.index.get_loc(i)]), 2),
            })
        for i, row in test_df.iterrows():
            chart_points.append({
                "date": row["date_str"],
                "label": row["quarter_label"],
                "split": "test",
                "actual": round(float(row["target"]), 2),
                "predicted": round(float(test_preds[test_df.index.get_loc(i)]), 2),
            })

        if next_forecast is not None and next_label is not None:
            chart_points.append({
                "date": "Next Horizon",
                "label": next_label,
                "split": "forecast",
                "actual": None,
                "predicted": next_forecast,
                "interval_low": next_interval_low,
                "interval_high": next_interval_high,
            })

        # Empirical Phillips Curve scatter points
        phillips_points = []
        for _, row in model_ready.iterrows():
            phillips_points.append({
                "unemployment": round(float(row["unemployment"]), 2),
                "inflation": round(float(row["inflation_lag"]), 2),
                "period": row["quarter_label"],
            })

        # Fit simple OLS on Phillips Curve for empirical slope
        ols_slope = -0.35
        ols_intercept = 4.2
        if len(phillips_points) >= 10:
            u_arr = np.array([p["unemployment"] for p in phillips_points]).reshape(-1, 1)
            pi_arr = np.array([p["inflation"] for p in phillips_points])
            ols = LinearRegression().fit(u_arr, pi_arr)
            ols_slope = round(float(ols.coef_[0]), 3)
            ols_intercept = round(float(ols.intercept_), 3)

        return {
            "country": SUPPORTED_COUNTRIES["USA"],
            "frequency": "Quarterly",
            "is_quarterly_native": True,
            "target_variable": "Next-Quarter CPI Inflation (YoY %)",
            "alpha": alpha,
            "test_ratio": test_ratio,
            "features_used": available_features,
            "metrics": {
                "test_mae": round(test_mae, 3),
                "test_rmse": round(test_rmse, 3),
                "test_r2": round(test_r2, 3),
                "train_mae": round(train_mae, 3),
                "train_rmse": round(train_rmse, 3),
                "baseline_mae": round(base_mae, 3),
                "baseline_rmse": round(base_rmse, 3),
                "beats_baseline": beats_baseline,
                "total_observations": n_samples,
                "train_size": len(train_df),
                "test_size": len(test_df),
                "train_period": f"{train_df['quarter_label'].iloc[0]} – {train_df['quarter_label'].iloc[-1]}",
                "test_period": f"{test_df['quarter_label'].iloc[0]} – {test_df['quarter_label'].iloc[-1]}",
            },
            "next_forecast": {
                "target_period": next_label,
                "point_forecast": next_forecast,
                "confidence_95": {
                    "low": next_interval_low,
                    "high": next_interval_high,
                    "margin_error": round(1.96 * test_rmse, 2),
                },
            },
            "coefficients": coef_records,
            "chart_data": chart_points,
            "phillips_curve": {
                "scatter": phillips_points,
                "ols_slope": ols_slope,
                "ols_intercept": ols_intercept,
                "interpretation": (
                    f"Empirical Phillips Curve OLS slope: β = {ols_slope:.3f}. "
                    "Note: In accordance with the Lucas Critique and Friedman-Phelps expectations theory, "
                    "this observational trade-off does not prove causation or establish an exploitable policy lever."
                ),
            },
        }

    def _forecast_annual_country(
        self, country_code: str, alpha: float, test_ratio: float, features: list[str]
    ) -> dict[str, Any]:
        """Annual frequency forecasting for countries without quarterly reporting."""
        profile = data_service.get_country_profile(country_code)
        cpi_s = {r["year"]: r["value"] for r in profile["series"].get("FP.CPI.TOTL.ZG", [])}
        gdp_s = {r["year"]: r["value"] for r in profile["series"].get("NY.GDP.MKTP.KD.ZG", [])}
        uem_s = {r["year"]: r["value"] for r in profile["series"].get("SL.UEM.TOTL.ZS", [])}
        rinr_s = {r["year"]: r["value"] for r in profile["series"].get("FR.INR.RINR", [])}

        years = sorted(set(cpi_s.keys()).intersection(gdp_s.keys()).intersection(uem_s.keys()))
        records = []
        for y in years:
            records.append({
                "year": y,
                "date_str": f"{y}-12-31",
                "label": f"{y}",
                "inflation_lag": cpi_s[y],
                "gdp_growth": gdp_s[y],
                "unemployment": uem_s[y],
                "interest_rate": rinr_s.get(y, profile["policy_rate"]["value"]),
            })

        df = pd.DataFrame(records)
        df["target"] = df["inflation_lag"].shift(-1)

        available_features = [f for f in features if f in df.columns]
        model_ready = df.dropna(subset=["target"] + available_features).copy().reset_index(drop=True)
        unseen_row = df[df["target"].isna()].copy()

        n_samples = len(model_ready)
        if n_samples < 15:
            raise ValueError(f"Insufficient annual samples ({n_samples} < 15 required) for {country_code}.")

        split_idx = int(n_samples * (1.0 - test_ratio))
        split_idx = max(10, min(split_idx, n_samples - 3))

        train_df = model_ready.iloc[:split_idx].copy()
        test_df = model_ready.iloc[split_idx:].copy()

        X_train_raw = train_df[available_features].values
        y_train = train_df["target"].values
        X_test_raw = test_df[available_features].values
        y_test = test_df["target"].values

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_raw)
        X_test_scaled = scaler.transform(X_test_raw)

        model = Ridge(alpha=alpha)
        model.fit(X_train_scaled, y_train)

        train_preds = model.predict(X_train_scaled)
        test_preds = model.predict(X_test_scaled)

        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_r2 = float(r2_score(y_test, test_preds))

        baseline_preds = test_df["inflation_lag"].values
        base_mae = float(mean_absolute_error(y_test, baseline_preds))
        base_rmse = float(np.sqrt(mean_squared_error(y_test, baseline_preds)))

        beats_baseline = test_rmse <= base_rmse

        coef_records = []
        for feat, coef in zip(available_features, model.coef_):
            meta = FEATURE_METADATA.get(feat, {"name": feat, "role": "Macro Predictor", "description": ""})
            coef_records.append({
                "feature": feat,
                "name": meta["name"],
                "role": meta["role"],
                "coefficient": round(float(coef), 4),
                "abs_weight": round(float(abs(coef)), 4),
                "direction": "Upward pressure (+)" if coef > 0 else "Downward pressure (-)",
                "description": meta["description"],
            })
        coef_records = sorted(coef_records, key=lambda x: x["abs_weight"], reverse=True)

        next_forecast = None
        next_label = None
        next_interval_low = None
        next_interval_high = None

        if not unseen_row.empty:
            latest_feat_vals = unseen_row[available_features].values[-1:]
            latest_scaled = scaler.transform(latest_feat_vals)
            next_forecast = round(float(model.predict(latest_scaled)[0]), 2)
            last_yr = int(unseen_row["year"].iloc[-1])
            next_label = f"Year {last_yr + 1}"
            next_interval_low = round(next_forecast - 1.96 * test_rmse, 2)
            next_interval_high = round(next_forecast + 1.96 * test_rmse, 2)

        chart_points = []
        for i, row in train_df.iterrows():
            chart_points.append({
                "date": str(row["year"]),
                "label": str(row["year"]),
                "split": "train",
                "actual": round(float(row["target"]), 2),
                "predicted": round(float(train_preds[train_df.index.get_loc(i)]), 2),
            })
        for i, row in test_df.iterrows():
            chart_points.append({
                "date": str(row["year"]),
                "label": str(row["year"]),
                "split": "test",
                "actual": round(float(row["target"]), 2),
                "predicted": round(float(test_preds[test_df.index.get_loc(i)]), 2),
            })

        if next_forecast is not None and next_label is not None:
            chart_points.append({
                "date": next_label,
                "label": next_label,
                "split": "forecast",
                "actual": None,
                "predicted": next_forecast,
                "interval_low": next_interval_low,
                "interval_high": next_interval_high,
            })

        phillips_points = [
            {"unemployment": round(float(r["unemployment"]), 2), "inflation": round(float(r["inflation_lag"]), 2), "period": str(r["year"])}
            for _, r in model_ready.iterrows()
        ]

        ols_slope = -0.25
        ols_intercept = 5.0
        if len(phillips_points) >= 8:
            u_arr = np.array([p["unemployment"] for p in phillips_points]).reshape(-1, 1)
            pi_arr = np.array([p["inflation"] for p in phillips_points])
            ols = LinearRegression().fit(u_arr, pi_arr)
            ols_slope = round(float(ols.coef_[0]), 3)
            ols_intercept = round(float(ols.intercept_), 3)

        return {
            "country": SUPPORTED_COUNTRIES.get(country_code, {"name": country_code, "flag": "🌐"}),
            "frequency": "Annual",
            "is_quarterly_native": False,
            "frequency_disclaimer": (
                f"Notice: World Bank indicators for {country_code} are published at an annual frequency. "
                "Per econometric integrity guidelines, quarterly interpolation without high-frequency source data "
                "creates artificial autocorrelation. This model therefore forecasts next-year inflation (t+1)."
            ),
            "target_variable": "Next-Year CPI Inflation (Annual %)",
            "alpha": alpha,
            "test_ratio": test_ratio,
            "features_used": available_features,
            "metrics": {
                "test_mae": round(test_mae, 3),
                "test_rmse": round(test_rmse, 3),
                "test_r2": round(test_r2, 3),
                "baseline_mae": round(base_mae, 3),
                "baseline_rmse": round(base_rmse, 3),
                "beats_baseline": beats_baseline,
                "total_observations": n_samples,
                "train_size": len(train_df),
                "test_size": len(test_df),
                "train_period": f"{train_df['year'].iloc[0]} – {train_df['year'].iloc[-1]}",
                "test_period": f"{test_df['year'].iloc[0]} – {test_df['year'].iloc[-1]}",
            },
            "next_forecast": {
                "target_period": next_label,
                "point_forecast": next_forecast,
                "confidence_95": {
                    "low": next_interval_low,
                    "high": next_interval_high,
                    "margin_error": round(1.96 * test_rmse, 2),
                },
            },
            "coefficients": coef_records,
            "chart_data": chart_points,
            "phillips_curve": {
                "scatter": phillips_points,
                "ols_slope": ols_slope,
                "ols_intercept": ols_intercept,
                "interpretation": (
                    f"Empirical Phillips Curve OLS slope: β = {ols_slope:.3f}. "
                    "Empirical non-causal association between unemployment and inflation."
                ),
            },
        }


models_service = ModelsService()
