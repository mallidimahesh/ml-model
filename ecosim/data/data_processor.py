"""Macroeconomic Data Processor for EcoSim.

Harmonizes multi-frequency economic series (monthly and quarterly),
calculates derived economic metrics (Misery Index, Approximate Real Rate),
and prepares strictly aligned lagged features for Ridge Regression forecasting
without lookahead data leakage.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def harmonize_macro_series(raw_series_dict: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Harmonize raw series into a single monthly chronological DataFrame.

    Aggregation & Alignment Rules:
    1. Monthly series (CPIAUCSL, UNRATE, FEDFUNDS, GS10) are aligned on the first day of each month (MS).
    2. Quarterly series (GDPC1) is aligned to the quarter-start month, then forward-filled for at most
       2 subsequent months of that specific quarter (limit=2). This reflects empirical information arrival
       without lookahead interpolation or fabricating future unreleased quarters.

    Args:
        raw_series_dict: Dictionary mapping series IDs to DataFrames with ['date', 'value'].

    Returns:
        pd.DataFrame: Clean monthly time series sorted chronologically.
    """
    cleaned_frames = {}

    for sid, df in raw_series_dict.items():
        if df is None or df.empty or "date" not in df.columns or "value" not in df.columns:
            continue
        s = df.copy()
        s["date"] = pd.to_datetime(s["date"])
        s = s.sort_values("date").drop_duplicates(subset=["date"])
        # Standardize date to Month Start (MS)
        s["month_date"] = s["date"].dt.to_period("M").dt.to_timestamp()
        grouped = s.groupby("month_date")["value"].last()
        cleaned_frames[sid] = grouped

    if not cleaned_frames:
        return pd.DataFrame()

    merged = pd.DataFrame(cleaned_frames)
    merged = merged.sort_index()

    # Forward fill quarterly GDP within its 3-month window (limit=2), preventing fabrication of future quarters
    if "GDPC1" in merged.columns:
        merged["GDPC1"] = merged["GDPC1"].ffill(limit=2)

    # Clean missing values: drop early warmup months where series have not started
    merged = merged.dropna(subset=[col for col in ["CPIAUCSL", "UNRATE", "FEDFUNDS"] if col in merged.columns])
    merged = merged.reset_index().rename(columns={"month_date": "date"})

    return merged


def calculate_derived_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate YoY inflation, real interest rate, misery index, and term spread.

    Formulas:
    - Year-over-Year Inflation (%):
        pi_t = ((CPI_t - CPI_{t-12}) / CPI_{t-12}) * 100
    - Misery Index (%):
        Misery_t = pi_t + Unemployment_t
    - Approximate Real Interest Rate (%):
        r_real_t = FedFunds_t - pi_t  (Fisher equation approximation based on observed inflation)
    - 10Y-FedFunds Yield Spread (%):
        Spread_t = GS10_t - FedFunds_t
    - Real GDP Growth YoY (%):
        GDP_Growth_t = ((GDP_t - GDP_{t-12}) / GDP_{t-12}) * 100

    Args:
        df: Harmonized monthly DataFrame containing raw series.

    Returns:
        pd.DataFrame: Augmented DataFrame with derived indicators.
    """
    out = df.copy()

    # Year-over-Year Inflation from CPI (12-month lag)
    if "CPIAUCSL" in out.columns:
        out["inflation_yoy"] = (
            (out["CPIAUCSL"] - out["CPIAUCSL"].shift(12)) / out["CPIAUCSL"].shift(12) * 100
        )
    else:
        out["inflation_yoy"] = np.nan

    # Derived: Misery Index = Inflation + Unemployment
    if "inflation_yoy" in out.columns and "UNRATE" in out.columns:
        out["misery_index"] = out["inflation_yoy"] + out["UNRATE"]
    else:
        out["misery_index"] = np.nan

    # Derived: Approximate Real Interest Rate = Fed Funds - YoY Inflation
    if "FEDFUNDS" in out.columns and "inflation_yoy" in out.columns:
        out["real_interest_rate"] = out["FEDFUNDS"] - out["inflation_yoy"]
    else:
        out["real_interest_rate"] = np.nan

    # Yield Spread: 10-Year Treasury Yield - Fed Funds Rate
    if "GS10" in out.columns and "FEDFUNDS" in out.columns:
        out["yield_spread"] = out["GS10"] - out["FEDFUNDS"]
    else:
        out["yield_spread"] = np.nan

    # Real GDP YoY growth (12-month lag in monthly harmonized frame)
    if "GDPC1" in out.columns:
        out["gdp_growth_yoy"] = (
            (out["GDPC1"] - out["GDPC1"].shift(12)) / out["GDPC1"].shift(12) * 100
        )
    else:
        out["gdp_growth_yoy"] = np.nan

    return out


def prepare_quarterly_forecasting_dataset(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], str]:
    """Construct quarterly dataset to predict next-quarter YoY inflation.

    Safe Time-Series Protocol respecting data frequency differences:
    - Real GDP is inherently a quarterly series.
    - Monthly series (CPI, Unemployment, Fed Funds Rate) are averaged across the months of each quarter.
    - YoY growth rates are computed using 4-quarter seasonal differences.
    - Target: Next-quarter YoY inflation (q+1): y_q = inflation_yoy_{q+1}.
    - Features: purely contemporaneous or lagged variables observed at or before quarter q:
      1. gdp_growth_yoy: YoY Real GDP Growth (%)
      2. inflation_yoy: YoY Inflation Rate (%)
      3. UNRATE: Civilian Unemployment Rate (%)
      4. FEDFUNDS: Effective Federal Funds Rate (%)
    - No future data (q+1 or beyond) enters feature matrix X_q.

    Returns:
        tuple: (processed_clean_df, feature_column_names, target_column_name)
    """
    if df.empty or "date" not in df.columns:
        return pd.DataFrame(), [], ""

    data = df.copy()
    data["quarter_period"] = pd.to_datetime(data["date"]).dt.to_period("Q")

    # Aggregate to quarterly frequency
    agg_dict = {
        "date": "last",
        "GDPC1": "last",
        "CPIAUCSL": "mean",
        "UNRATE": "mean",
        "FEDFUNDS": "mean",
    }
    valid_agg = {k: v for k, v in agg_dict.items() if k in data.columns}
    quarterly = data.groupby("quarter_period").agg(valid_agg).reset_index()

    # Calculate quarterly YoY rates (4 quarters per year)
    if "GDPC1" in quarterly.columns:
        quarterly["gdp_growth_yoy"] = (
            (quarterly["GDPC1"] - quarterly["GDPC1"].shift(4)) / quarterly["GDPC1"].shift(4) * 100
        )
    else:
        quarterly["gdp_growth_yoy"] = np.nan

    if "CPIAUCSL" in quarterly.columns:
        quarterly["inflation_yoy"] = (
            (quarterly["CPIAUCSL"] - quarterly["CPIAUCSL"].shift(4)) / quarterly["CPIAUCSL"].shift(4) * 100
        )
    else:
        quarterly["inflation_yoy"] = np.nan

    # Target: Next-quarter YoY inflation (shift by -1 quarter)
    target_col = "target_next_quarter_inflation"
    quarterly[target_col] = quarterly["inflation_yoy"].shift(-1)

    feature_cols = [
        "gdp_growth_yoy",
        "inflation_yoy",
        "UNRATE",
        "FEDFUNDS",
    ]

    # Clean rows: drop warmup rows where 4-quarter lag features are NaN
    clean_data = quarterly.dropna(subset=[f for f in feature_cols if f in quarterly.columns]).copy()
    clean_data["date"] = pd.to_datetime(clean_data["date"])
    clean_data["quarter_label"] = clean_data["quarter_period"].apply(
        lambda p: f"Q{p.quarter} {p.year}"
    )
    clean_data = clean_data.sort_values("date").reset_index(drop=True)

    return clean_data, feature_cols, target_col


# Provide alias for backward compatibility
prepare_forecasting_dataset = prepare_quarterly_forecasting_dataset
