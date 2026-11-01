"""Economic Regime Analysis, Inflation Decomposition, and NBER Chronology for EcoSim.

Provides:
1. Official US NBER Business-Cycle Chronology with recession intervals and metadata.
2. Transparent statistical slowdown rules for Indian macroeconomic series.
3. Regime-level descriptive statistics (Expansions vs. Recessions / Slowdowns).
4. Classical additive time series decomposition (Trend, Seasonal, Residual) for monthly CPI.
5. Strict monthly continuity validation to prevent arbitrary gap-filling.
6. Historical inflation turning point detection (peaks and troughs).
7. Authentic MoSPI PLFS Urban Quarterly Labour dataset for India Phillips Curve analysis.
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. OFFICIAL US NBER BUSINESS-CYCLE CHRONOLOGY
# Authoritative Source: National Bureau of Economic Research (NBER)
# Business Cycle Dating Committee (https://www.nber.org/research/business-cycle-dating)
# ==============================================================================

US_NBER_RECESSIONS: list[dict[str, Any]] = [
    {
        "name": "1973–75 Oil Shock & Stagflation",
        "start": "1973-11-01",
        "end": "1975-03-01",
        "duration_months": 16,
        "description": "Triggered by the 1973 OPEC oil embargo, quadrupling crude oil prices and ending the post-WWII economic boom with simultaneous high inflation and deep contraction.",
    },
    {
        "name": "1980 Energy Crisis Contraction",
        "start": "1980-01-01",
        "end": "1980-07-01",
        "duration_months": 6,
        "description": "Short contraction caused by the Iranian revolution oil shock and aggressive monetary tightening by the Federal Reserve under Paul Volcker.",
    },
    {
        "name": "1981–82 Volcker Disinflation Recession",
        "start": "1981-07-01",
        "end": "1982-11-01",
        "duration_months": 16,
        "description": "Severe contraction induced by the Volcker Fed raising the Fed Funds rate above 20% to break embedded double-digit inflation, resulting in civilian unemployment peaking at 10.8%.",
    },
    {
        "name": "1990–91 Gulf War Recession",
        "start": "1990-07-01",
        "end": "1991-03-01",
        "duration_months": 8,
        "description": "Triggered by the Iraqi invasion of Kuwait, an oil price spike, commercial banking distress following the Savings and Loan crisis, and weakened consumer sentiment.",
    },
    {
        "name": "2001 Dot-Com Bust & Post-9/11",
        "start": "2001-03-01",
        "end": "2001-11-01",
        "duration_months": 8,
        "description": "Collapse of speculative technology equities, steep reductions in corporate capital expenditure, and the immediate economic shock of the September 11 terrorist attacks.",
    },
    {
        "name": "2007–09 Great Financial Crisis (GFC)",
        "start": "2007-12-01",
        "end": "2009-06-01",
        "duration_months": 18,
        "description": "Deepest post-WWII contraction prior to 2020, triggered by subprime mortgage defaults, nationwide housing price collapse, Lehman Brothers collapse, and global credit market seizure.",
    },
    {
        "name": "2020 COVID-19 Pandemic Shock",
        "start": "2020-02-01",
        "end": "2020-04-01",
        "duration_months": 2,
        "description": "Sharpest and shortest recession in recorded US history, caused by mandatory global containment lockdowns and social-distancing measures to curb SARS-CoV-2.",
    },
]

# ==============================================================================
# 2. TRANSPARENT INDIAN GROWTH SLOWDOWN REGIMES
# Statistical Rule: >= 2 consecutive quarters of Real GDP YoY growth below 5.0%
# or negative growth (technical contraction).
# NOTE: India has no official recession-dating committee equivalent to NBER.
# These episodes are classified strictly as analytical growth slowdown regimes.
# ==============================================================================

INDIA_SLOWDOWN_REGIMES: list[dict[str, Any]] = [
    {
        "name": "2012–13 Investment Deceleration & Twin Balance Sheet Stress",
        "start": "2012-04-01",
        "end": "2013-03-31",
        "duration_quarters": 4,
        "rule": "Real GDP YoY growth below 5.0% for 4 consecutive quarters (4.5%–4.9%).",
        "description": "Post-crisis structural slowdown characterized by corporate debt overhang, stressed public-sector bank balance sheets, project implementation delays, and high headline inflation.",
    },
    {
        "name": "2019–20 Pre-Pandemic Deceleration & NBFC Liquidity Squeeze",
        "start": "2019-01-01",
        "end": "2020-03-31",
        "duration_quarters": 5,
        "rule": "Real GDP YoY growth below 5.0% (down to 3.1% in Q4 FY20) for 5 consecutive quarters.",
        "description": "Gradual pre-pandemic growth deceleration following the IL&FS default, non-bank financial company (NBFC) credit freeze, automotive sales slump, and sluggish rural consumption.",
    },
    {
        "name": "2020 COVID-19 National Lockdown Contraction",
        "start": "2020-04-01",
        "end": "2020-12-31",
        "duration_quarters": 3,
        "rule": "Two consecutive quarters of negative Real GDP YoY growth (-23.1% in Q1, -6.6% in Q2 FY21).",
        "description": "Severe economic contraction caused by the nationwide lockdown announced on March 24, 2020, completely halting industrial and service activities during Q1 FY2020-21.",
    },
]


def get_nber_recessions() -> list[dict[str, Any]]:
    """Return the official NBER business cycle recession chronology."""
    return US_NBER_RECESSIONS


def get_india_slowdowns() -> list[dict[str, Any]]:
    """Return documented Indian analytical growth slowdown regimes."""
    return INDIA_SLOWDOWN_REGIMES


# ==============================================================================
# 3. REGIME CLASSIFICATION & DESCRIPTIVE STATISTICS
# ==============================================================================

def classify_us_regimes(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Classify monthly US observations into NBER Recession vs NBER Expansion."""
    out = df.copy()
    if date_col not in out.columns or out.empty:
        return out

    out[date_col] = pd.to_datetime(out[date_col])
    out["is_recession"] = False
    out["recession_name"] = "NBER Expansion"

    for rec in US_NBER_RECESSIONS:
        start_dt = pd.to_datetime(rec["start"])
        end_dt = pd.to_datetime(rec["end"])
        mask = (out[date_col] >= start_dt) & (out[date_col] <= end_dt)
        out.loc[mask, "is_recession"] = True
        out.loc[mask, "recession_name"] = rec["name"]

    out["regime_label"] = np.where(out["is_recession"], "NBER Recession", "NBER Expansion")
    return out


def compute_us_regime_statistics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute indicator averages and behavior during US Expansions vs Recessions.

    Returns:
        tuple: (regime_summary_df, recession_episodes_df)
    """
    classified = classify_us_regimes(df)
    if classified.empty or "regime_label" not in classified.columns:
        return pd.DataFrame(), pd.DataFrame()

    indicators = [
        ("gdp_growth_yoy", "Real GDP Growth YoY (%)"),
        ("inflation_yoy", "CPI Inflation YoY (%)"),
        ("UNRATE", "Civilian Unemployment Rate (%)"),
        ("FEDFUNDS", "Federal Funds Effective Rate (%)"),
        ("GS10", "10-Year Treasury Yield (%)"),
        ("misery_index", "Misery Index (Inflation + Unemp)"),
    ]

    summary_rows = []
    for col, name in indicators:
        if col in classified.columns:
            s_exp = classified[classified["regime_label"] == "NBER Expansion"][col].dropna()
            s_rec = classified[classified["regime_label"] == "NBER Recession"][col].dropna()

            mean_exp = s_exp.mean() if not s_exp.empty else np.nan
            mean_rec = s_rec.mean() if not s_rec.empty else np.nan
            delta = mean_rec - mean_exp if not np.isnan(mean_rec) and not np.isnan(mean_exp) else np.nan

            summary_rows.append({
                "Indicator": name,
                "Expansion Mean": round(mean_exp, 2) if not np.isnan(mean_exp) else "N/A",
                "Recession Mean": round(mean_rec, 2) if not np.isnan(mean_rec) else "N/A",
                "Regime Delta (Rec − Exp)": round(delta, 2) if not np.isnan(delta) else "N/A",
                "Expansion N": len(s_exp),
                "Recession N": len(s_rec),
            })

    df_summary = pd.DataFrame(summary_rows)

    # Detailed table for each official recession episode within available data range
    min_date = classified["date"].min()
    max_date = classified["date"].max()

    episode_rows = []
    for rec in US_NBER_RECESSIONS:
        r_start = pd.to_datetime(rec["start"])
        r_end = pd.to_datetime(rec["end"])

        # Check if episode overlaps with dataset
        if r_end < min_date or r_start > max_date:
            continue

        sub = classified[(classified["date"] >= r_start) & (classified["date"] <= r_end)]
        if sub.empty:
            continue

        unemp_start = sub["UNRATE"].dropna().iloc[0] if "UNRATE" in sub and not sub["UNRATE"].dropna().empty else np.nan
        unemp_peak = sub["UNRATE"].dropna().max() if "UNRATE" in sub and not sub["UNRATE"].dropna().empty else np.nan
        cpi_start = sub["inflation_yoy"].dropna().iloc[0] if "inflation_yoy" in sub and not sub["inflation_yoy"].dropna().empty else np.nan
        cpi_end = sub["inflation_yoy"].dropna().iloc[-1] if "inflation_yoy" in sub and not sub["inflation_yoy"].dropna().empty else np.nan
        fed_start = sub["FEDFUNDS"].dropna().iloc[0] if "FEDFUNDS" in sub and not sub["FEDFUNDS"].dropna().empty else np.nan
        fed_end = sub["FEDFUNDS"].dropna().iloc[-1] if "FEDFUNDS" in sub and not sub["FEDFUNDS"].dropna().empty else np.nan
        gdp_trough = sub["gdp_growth_yoy"].dropna().min() if "gdp_growth_yoy" in sub and not sub["gdp_growth_yoy"].dropna().empty else np.nan

        episode_rows.append({
            "Recession Episode": rec["name"],
            "Official Period": f"{rec['start'][:7]} to {rec['end'][:7]}",
            "Duration (Months)": rec["duration_months"],
            "Observed Months": len(sub),
            "Unemployment Start → Peak": f"{unemp_start:.1f}% → {unemp_peak:.1f}%" if not np.isnan(unemp_start) and not np.isnan(unemp_peak) else "N/A",
            "Inflation Start → End": f"{cpi_start:.1f}% → {cpi_end:.1f}%" if not np.isnan(cpi_start) and not np.isnan(cpi_end) else "N/A",
            "Fed Funds Policy Shift": f"{fed_start:.2f}% → {fed_end:.2f}%" if not np.isnan(fed_start) and not np.isnan(fed_end) else "N/A",
            "GDP Growth Trough": f"{gdp_trough:.2f}%" if not np.isnan(gdp_trough) else "N/A",
        })

    df_episodes = pd.DataFrame(episode_rows)
    return df_summary, df_episodes


def compute_india_slowdown_statistics(
    df_gdp: pd.DataFrame,
    df_cpi: pd.DataFrame | None = None,
    df_iip: pd.DataFrame | None = None,
    df_wacr: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute indicator averages during Indian Analytical Slowdowns vs Trend Growth.

    Returns:
        tuple: (summary_df, slowdown_episodes_df)
    """
    if df_gdp.empty or "date" not in df_gdp.columns:
        return pd.DataFrame(), pd.DataFrame()

    g = df_gdp.copy()
    g["date"] = pd.to_datetime(g["date"])
    g = g.sort_values("date").reset_index(drop=True)

    # Compute quarterly Real GDP YoY Growth
    if "real_gdp_crores" in g.columns:
        g["gdp_growth_yoy"] = (g["real_gdp_crores"] - g["real_gdp_crores"].shift(4)) / g["real_gdp_crores"].shift(4) * 100
    elif "real_gdp_inr" in g.columns:
        g["gdp_growth_yoy"] = (g["real_gdp_inr"] - g["real_gdp_inr"].shift(4)) / g["real_gdp_inr"].shift(4) * 100

    g["is_slowdown"] = False
    g["slowdown_name"] = "Trend Growth"

    for reg in INDIA_SLOWDOWN_REGIMES:
        s_dt = pd.to_datetime(reg["start"])
        e_dt = pd.to_datetime(reg["end"])
        mask = (g["date"] >= s_dt) & (g["date"] <= e_dt)
        g.loc[mask, "is_slowdown"] = True
        g.loc[mask, "slowdown_name"] = reg["name"]

    g["regime_label"] = np.where(g["is_slowdown"], "Analytical Slowdown", "Trend Growth")

    # Merge CPI, IIP, WACR aggregated to quarters
    merged = g[["date", "gdp_growth_yoy", "is_slowdown", "slowdown_name", "regime_label"]].copy()

    if df_cpi is not None and not df_cpi.empty and "date" in df_cpi.columns and "cpi_index" in df_cpi.columns:
        c = df_cpi.copy()
        c["date"] = pd.to_datetime(c["date"])
        c = c.sort_values("date").reset_index(drop=True)
        c["cpi_yoy"] = (c["cpi_index"] - c["cpi_index"].shift(12)) / c["cpi_index"].shift(12) * 100
        c["quarter_date"] = c["date"].dt.to_period("Q").dt.to_timestamp()
        c_q = c.groupby("quarter_date")["cpi_yoy"].mean().reset_index()
        merged = pd.merge_asof(merged.sort_values("date"), c_q.sort_values("quarter_date"), left_on="date", right_on="quarter_date", direction="nearest")

    if df_iip is not None and not df_iip.empty and "date" in df_iip.columns and "iip_index" in df_iip.columns:
        ip = df_iip.copy()
        ip["date"] = pd.to_datetime(ip["date"])
        ip = ip.sort_values("date").reset_index(drop=True)
        ip["iip_yoy"] = (ip["iip_index"] - ip["iip_index"].shift(12)) / ip["iip_index"].shift(12) * 100
        ip["quarter_date"] = ip["date"].dt.to_period("Q").dt.to_timestamp()
        ip_q = ip.groupby("quarter_date")["iip_yoy"].mean().reset_index()
        merged = pd.merge_asof(merged.sort_values("date"), ip_q.sort_values("quarter_date"), left_on="date", right_on="quarter_date", direction="nearest")

    if df_wacr is not None and not df_wacr.empty and "date" in df_wacr.columns and "policy_rate" in df_wacr.columns:
        w = df_wacr.copy()
        w["date"] = pd.to_datetime(w["date"])
        w["quarter_date"] = w["date"].dt.to_period("Q").dt.to_timestamp()
        w_q = w.groupby("quarter_date")["policy_rate"].mean().reset_index()
        merged = pd.merge_asof(merged.sort_values("date"), w_q.sort_values("quarter_date"), left_on="date", right_on="quarter_date", direction="nearest")

    indicators = [
        ("gdp_growth_yoy", "Quarterly Real GDP Growth YoY (%)"),
        ("cpi_yoy", "Quarterly CPI Combined YoY (%)"),
        ("iip_yoy", "Quarterly Industrial Production (IIP) YoY (%)"),
        ("policy_rate", "Weighted Average Call Rate / WACR (% p.a.)"),
    ]

    summary_rows = []
    for col, name in indicators:
        if col in merged.columns:
            s_trend = merged[merged["regime_label"] == "Trend Growth"][col].dropna()
            s_slow = merged[merged["regime_label"] == "Analytical Slowdown"][col].dropna()

            mean_trend = s_trend.mean() if not s_trend.empty else np.nan
            mean_slow = s_slow.mean() if not s_slow.empty else np.nan
            delta = mean_slow - mean_trend if not np.isnan(mean_slow) and not np.isnan(mean_trend) else np.nan

            summary_rows.append({
                "Indicator": name,
                "Trend Growth Mean": round(mean_trend, 2) if not np.isnan(mean_trend) else "N/A",
                "Slowdown Mean": round(mean_slow, 2) if not np.isnan(mean_slow) else "N/A",
                "Regime Delta (Slow − Trend)": round(delta, 2) if not np.isnan(delta) else "N/A",
                "Trend Quarters": len(s_trend),
                "Slowdown Quarters": len(s_slow),
            })

    df_summary = pd.DataFrame(summary_rows)

    # Episode breakdown table
    ep_rows = []
    for reg in INDIA_SLOWDOWN_REGIMES:
        s_dt = pd.to_datetime(reg["start"])
        e_dt = pd.to_datetime(reg["end"])
        sub = merged[(merged["date"] >= s_dt) & (merged["date"] <= e_dt)]
        if sub.empty:
            continue

        gdp_trough = sub["gdp_growth_yoy"].dropna().min() if "gdp_growth_yoy" in sub else np.nan
        gdp_mean = sub["gdp_growth_yoy"].dropna().mean() if "gdp_growth_yoy" in sub else np.nan
        cpi_mean = sub["cpi_yoy"].dropna().mean() if "cpi_yoy" in sub else np.nan

        ep_rows.append({
            "Slowdown Episode": reg["name"],
            "Period Range": f"{reg['start'][:7]} to {reg['end'][:7]}",
            "Quarters": reg["duration_quarters"],
            "Statistical Rule": reg["rule"],
            "Average GDP Growth": f"{gdp_mean:.2f}%" if not np.isnan(gdp_mean) else "N/A",
            "GDP Growth Trough": f"{gdp_trough:.2f}%" if not np.isnan(gdp_trough) else "N/A",
            "Average CPI YoY": f"{cpi_mean:.2f}%" if not np.isnan(cpi_mean) else "N/A",
        })

    df_episodes = pd.DataFrame(ep_rows)
    return df_summary, df_episodes


# ==============================================================================
# 4. INFLATION DECOMPOSITION & FREQUENCY VALIDATION
# ==============================================================================

def validate_monthly_continuity(df: pd.DataFrame, date_col: str = "date") -> tuple[bool, str, list[str]]:
    """Verify that a time series is genuinely monthly without missing calendar months.

    Args:
        df: DataFrame containing date column.
        date_col: Name of date column.

    Returns:
        tuple: (is_valid, validation_message, missing_dates_list)
    """
    if df.empty or date_col not in df.columns:
        return False, "DataFrame is empty or missing date column.", []

    dates = pd.to_datetime(df[date_col]).drop_duplicates().sort_values().reset_index(drop=True)
    if len(dates) < 24:
        return False, f"Insufficient observations for monthly seasonal decomposition ({len(dates)} < 24 minimum).", []

    # Generate expected regular monthly start dates between min and max
    min_date = dates.min().to_period("M").to_timestamp()
    max_date = dates.max().to_period("M").to_timestamp()
    expected_monthly = pd.date_range(start=min_date, end=max_date, freq="MS")

    # Map actual dates to Month Start
    actual_month_starts = set(dates.dt.to_period("M").dt.to_timestamp())
    missing = [d.strftime("%Y-%m") for d in expected_monthly if d not in actual_month_starts]

    if missing:
        msg = f"Non-continuous time series: detected {len(missing)} missing calendar month(s) between {min_date.strftime('%Y-%m')} and {max_date.strftime('%Y-%m')}."
        return False, msg, missing

    msg = f"Verified contiguous monthly series: {len(dates)} months ({min_date.strftime('%b %Y')} to {max_date.strftime('%b %Y')}) without missing intervals."
    return True, msg, []


def calculate_mom_yoy_inflation(
    df_cpi: pd.DataFrame,
    cpi_col: str = "cpi_index",
    date_col: str = "date",
) -> pd.DataFrame:
    """Calculate Month-on-Month (MoM) and Year-on-Year (YoY) inflation rates from CPI level.

    Formulas:
    - CPI Index Level: Raw price basket level (e.g. 1982-84=100 or 2012=100)
    - MoM Inflation (%): ((CPI_t - CPI_{t-1}) / CPI_{t-1}) * 100
    - YoY Inflation (%): ((CPI_t - CPI_{t-12}) / CPI_{t-12}) * 100
    - Annualized MoM (%): (((1 + MoM / 100) ^ 12) - 1) * 100
    """
    out = df_cpi.copy()
    if cpi_col not in out.columns or date_col not in out.columns:
        return out

    out[date_col] = pd.to_datetime(out[date_col])
    out = out.sort_values(date_col).reset_index(drop=True)

    out["inflation_mom"] = (out[cpi_col] - out[cpi_col].shift(1)) / out[cpi_col].shift(1) * 100
    out["inflation_yoy"] = (out[cpi_col] - out[cpi_col].shift(12)) / out[cpi_col].shift(12) * 100
    # Annualized MoM compounding
    out["inflation_mom_annualized"] = np.where(
        out["inflation_mom"].notna(),
        ((1 + out["inflation_mom"] / 100) ** 12 - 1) * 100,
        np.nan,
    )
    return out


def decompose_monthly_inflation_classical(
    series: pd.Series,
    dates: pd.Series,
    freq: int = 12,
) -> dict[str, Any]:
    """Perform classical additive time series decomposition (Trend + Seasonal + Residual).

    Mathematical Formulation:
    Y_t = Trend_t + Seasonal_t + Residual_t

    Steps:
    1. Trend_t is estimated via a 2x12 centered moving average filter to eliminate
       the 12-month annual seasonality.
    2. Detrended series: D_t = Y_t - Trend_t.
    3. Seasonal_t: Average detrended deviation for each calendar month (1..12),
       normalized so the 12 monthly factors sum exactly to zero (sum_m S_m = 0).
    4. Residual_t: Y_t - Trend_t - Seasonal_t.

    Returns:
        dict with keys: 'trend', 'seasonal', 'residual', 'seasonal_factors', 'variance_shares'
    """
    dates_clean = pd.to_datetime(dates).reset_index(drop=True)
    y = pd.Series(series.values, index=dates_clean).dropna()

    if len(y) < freq * 2:
        return {
            "error": f"Series length ({len(y)}) too short for seasonal decomposition (minimum {freq * 2} required).",
        }

    # Step 1: 2x12 Centered Moving Average for Trend
    # 12-month rolling mean centered, then 2-month rolling mean to align on exact integer steps
    ma12 = y.rolling(freq, center=True).mean()
    trend = ma12.rolling(2, center=True).mean().shift(-1)

    # Step 2: Detrended Series
    detrended = y - trend

    # Step 3: Monthly Seasonal Factor (normalized to zero sum across all 12 calendar months)
    months = y.index.month
    monthly_factors = detrended.groupby(months).mean()
    # Normalize to zero mean so seasonal component does not shift level
    norm_factors = monthly_factors - monthly_factors.mean()

    seasonal_series = pd.Series([norm_factors[m] for m in months], index=y.index)

    # Step 4: Residual Component
    residual = y - trend - seasonal_series

    # Step 5: Variance Contributions
    valid_mask = trend.notna() & residual.notna()
    var_total = float(np.var(y[valid_mask]))
    var_trend = float(np.var(trend[valid_mask]))
    var_seasonal = float(np.var(seasonal_series[valid_mask]))
    var_residual = float(np.var(residual[valid_mask]))

    variance_shares = {
        "trend_share": round((var_trend / var_total) * 100, 2) if var_total > 0 else 0.0,
        "seasonal_share": round((var_seasonal / var_total) * 100, 2) if var_total > 0 else 0.0,
        "residual_share": round((var_residual / var_total) * 100, 2) if var_total > 0 else 0.0,
    }

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seasonal_factors_dict = {
        month_names[m - 1]: round(float(norm_factors[m]), 3) for m in range(1, 13)
    }

    return {
        "dates": y.index,
        "observed": y,
        "trend": trend,
        "seasonal": seasonal_series,
        "residual": residual,
        "seasonal_factors": seasonal_factors_dict,
        "variance_shares": variance_shares,
        "n_obs": len(y),
    }


def detect_inflation_turning_points(
    df: pd.DataFrame,
    col: str = "inflation_yoy",
    date_col: str = "date",
    window: int = 7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Identify historical local peaks and troughs in CPI inflation.

    Uses a rolling window comparison to identify genuine local extrema.
    """
    clean = df[[date_col, col]].dropna().copy()
    if len(clean) < window * 2:
        return pd.DataFrame(), pd.DataFrame()

    clean[date_col] = pd.to_datetime(clean[date_col])
    clean = clean.sort_values(date_col).reset_index(drop=True)

    vals = clean[col].values
    n = len(vals)
    peaks_idx = []
    troughs_idx = []

    for i in range(window, n - window):
        center = vals[i]
        neighbors = vals[i - window : i + window + 1]
        if center == np.max(neighbors) and center > vals[i - 1] and center > vals[i + 1]:
            peaks_idx.append(i)
        elif center == np.min(neighbors) and center < vals[i - 1] and center < vals[i + 1]:
            troughs_idx.append(i)

    df_peaks = clean.iloc[peaks_idx].copy().rename(columns={col: "peak_inflation"})
    df_troughs = clean.iloc[troughs_idx].copy().rename(columns={col: "trough_inflation"})

    return df_peaks, df_troughs


# ==============================================================================
# 5. MOSPI PLFS URBAN QUARTERLY LABOUR DATASET FOR INDIA PHILLIPS CURVE
# Source: MoSPI NSSO Quarterly Bulletins of the Periodic Labour Force Survey (PLFS)
# Indicator: Urban Unemployment Rate (Age 15+, Current Weekly Status / CWS)
# Paired with RBI DBIE All-India CPI Combined YoY Inflation
# ==============================================================================

def load_india_quarterly_phillips_dataset() -> pd.DataFrame:
    """Official Quarterly Urban Unemployment Rate (PLFS CWS) paired with CPI YoY Inflation.

    Source:
    - Unemployment: MoSPI NSSO PLFS Urban Quarterly Bulletins (Q1 2018 to Q2 2024, 26 quarters).
    - Inflation: RBI DBIE CPI Combined All-India Base 2012=100 (Quarterly Average YoY).
    """
    records = [
        {"quarter": "2018-Q1", "date": "2018-03-31", "unrate": 9.8, "cpi_yoy": 4.44},
        {"quarter": "2018-Q2", "date": "2018-06-30", "unrate": 9.6, "cpi_yoy": 4.77},
        {"quarter": "2018-Q3", "date": "2018-09-30", "unrate": 9.7, "cpi_yoy": 3.88},
        {"quarter": "2018-Q4", "date": "2018-12-31", "unrate": 9.9, "cpi_yoy": 2.61},
        {"quarter": "2019-Q1", "date": "2019-03-31", "unrate": 9.3, "cpi_yoy": 2.51},
        {"quarter": "2019-Q2", "date": "2019-06-30", "unrate": 8.9, "cpi_yoy": 3.05},
        {"quarter": "2019-Q3", "date": "2019-09-30", "unrate": 8.4, "cpi_yoy": 3.52},
        {"quarter": "2019-Q4", "date": "2019-12-31", "unrate": 7.9, "cpi_yoy": 7.35},
        {"quarter": "2020-Q1", "date": "2020-03-31", "unrate": 9.1, "cpi_yoy": 6.67},
        {"quarter": "2020-Q2", "date": "2020-06-30", "unrate": 20.9, "cpi_yoy": 6.23},  # Lockdown peak
        {"quarter": "2020-Q3", "date": "2020-09-30", "unrate": 13.3, "cpi_yoy": 6.88},
        {"quarter": "2020-Q4", "date": "2020-12-31", "unrate": 10.3, "cpi_yoy": 6.37},
        {"quarter": "2021-Q1", "date": "2021-03-31", "unrate": 9.3, "cpi_yoy": 4.88},
        {"quarter": "2021-Q2", "date": "2021-06-30", "unrate": 12.6, "cpi_yoy": 5.58},  # Delta wave
        {"quarter": "2021-Q3", "date": "2021-09-30", "unrate": 9.8, "cpi_yoy": 5.08},
        {"quarter": "2021-Q4", "date": "2021-12-31", "unrate": 8.7, "cpi_yoy": 5.01},
        {"quarter": "2022-Q1", "date": "2022-03-31", "unrate": 8.2, "cpi_yoy": 6.34},
        {"quarter": "2022-Q2", "date": "2022-06-30", "unrate": 7.6, "cpi_yoy": 7.28},
        {"quarter": "2022-Q3", "date": "2022-09-30", "unrate": 7.2, "cpi_yoy": 7.04},
        {"quarter": "2022-Q4", "date": "2022-12-31", "unrate": 7.2, "cpi_yoy": 6.12},
        {"quarter": "2023-Q1", "date": "2023-03-31", "unrate": 6.8, "cpi_yoy": 6.16},
        {"quarter": "2023-Q2", "date": "2023-06-30", "unrate": 6.6, "cpi_yoy": 4.63},
        {"quarter": "2023-Q3", "date": "2023-09-30", "unrate": 6.6, "cpi_yoy": 6.42},
        {"quarter": "2023-Q4", "date": "2023-12-31", "unrate": 6.5, "cpi_yoy": 5.37},
        {"quarter": "2024-Q1", "date": "2024-03-31", "unrate": 6.7, "cpi_yoy": 4.97},
        {"quarter": "2024-Q2", "date": "2024-06-30", "unrate": 6.6, "cpi_yoy": 5.08},
    ]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df
