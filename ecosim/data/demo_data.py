"""Realistic historical US macroeconomic demonstration dataset for EcoSim.

Used when an active FRED API key is not supplied or during offline presentations.
Values reflect historical US macroeconomic benchmarks (1990-2024).
"""

from __future__ import annotations

import pandas as pd
import numpy as np


def generate_demo_macro_data() -> dict[str, pd.DataFrame]:
    """Generate realistic historical time-series for US macroeconomic indicators.

    Returns:
        dict: Mapping of FRED series IDs to DataFrames with columns ['date', 'value'].
    """
    # Monthly date range from 1990-01-01 to 2024-06-01
    dates_monthly = pd.date_range(start="1990-01-01", end="2024-06-01", freq="MS")
    n_months = len(dates_monthly)

    # Quarterly dates for GDP
    dates_quarterly = pd.date_range(start="1990-01-01", end="2024-06-01", freq="QS")
    n_quarters = len(dates_quarterly)

    # 1. Real GDP (GDPC1) - Billions of Chained 2017 Dollars (Quarterly: ~9,000 to ~22,500)
    # Secular upward growth with contractions in 1991, 2001, 2008-09, 2020
    t_q = np.linspace(0, 1, n_quarters)
    gdp_trend = 9500 + 13000 * t_q
    # Add historical recessions
    recessions_q = np.zeros(n_quarters)
    for i, d in enumerate(dates_quarterly):
        if 2008 <= d.year <= 2009:
            recessions_q[i] = -600
        elif d.year == 2020 and d.quarter == 2:
            recessions_q[i] = -1800
        elif d.year == 2020 and d.quarter >= 3:
            recessions_q[i] = -400
    gdp_noise = np.sin(np.linspace(0, 30, n_quarters)) * 100
    gdp_vals = np.round(gdp_trend + recessions_q + gdp_noise, 1)
    df_gdp = pd.DataFrame({"date": dates_quarterly, "value": gdp_vals})

    # 2. CPIAUCSL (CPI for All Urban Consumers) - Index 1982-1984=100 (~130 to ~315)
    t_m = np.linspace(0, 1, n_months)
    cpi_base = 130 * np.exp(0.88 * t_m)  # roughly 130 in 1990 to 314 in 2024
    # Post-2020 inflation surge
    cpi_bump = np.zeros(n_months)
    for i, d in enumerate(dates_monthly):
        if d.year >= 2021:
            cpi_bump[i] = (d.year - 2021 + d.month / 12) * 5.2
    cpi_vals = np.round(cpi_base + cpi_bump, 2)
    df_cpi = pd.DataFrame({"date": dates_monthly, "value": cpi_vals})

    # 3. Civilian Unemployment Rate (UNRATE) (%)
    unrate_vals = np.zeros(n_months)
    for i, d in enumerate(dates_monthly):
        yr = d.year
        if yr < 1993:
            unrate_vals[i] = 6.8 + 0.5 * np.sin(i * 0.1)
        elif yr < 2000:
            unrate_vals[i] = 5.2 - 0.15 * (yr - 1993)
        elif yr < 2003:
            unrate_vals[i] = 4.2 + 0.4 * (yr - 2000)
        elif yr < 2008:
            unrate_vals[i] = 5.0 - 0.1 * (yr - 2003)
        elif yr <= 2010:
            unrate_vals[i] = 5.0 + 2.4 * (yr - 2007) + 0.2 * np.sin(i * 0.2)
        elif yr < 2020:
            unrate_vals[i] = max(3.5, 9.8 - 0.65 * (yr - 2010))
        elif yr == 2020 and d.month in [4, 5, 6]:
            unrate_vals[i] = 14.7 if d.month == 4 else (13.2 if d.month == 5 else 11.0)
        elif yr == 2020:
            unrate_vals[i] = 7.5
        elif yr == 2021:
            unrate_vals[i] = 5.4 - 0.1 * d.month
        else:
            unrate_vals[i] = 3.7 + 0.2 * np.sin(i * 0.15)
    unrate_vals = np.clip(np.round(unrate_vals, 1), 3.0, 15.0)
    df_unrate = pd.DataFrame({"date": dates_monthly, "value": unrate_vals})

    # 4. Federal Funds Effective Rate (FEDFUNDS) (%)
    fedfunds_vals = np.zeros(n_months)
    for i, d in enumerate(dates_monthly):
        yr = d.year
        if yr < 1995:
            fedfunds_vals[i] = 5.5 - 0.5 * (yr - 1990)
        elif yr < 2001:
            fedfunds_vals[i] = 5.2 + 0.3 * np.sin(i * 0.05)
        elif yr < 2004:
            fedfunds_vals[i] = max(1.0, 5.0 - 1.2 * (yr - 2000))
        elif yr < 2008:
            fedfunds_vals[i] = min(5.25, 1.2 + 1.0 * (yr - 2003))
        elif yr < 2016:
            fedfunds_vals[i] = 0.15 + 0.05 * np.random.uniform(-0.1, 0.1)
        elif yr < 2019:
            fedfunds_vals[i] = 0.4 + 0.6 * (yr - 2015)
        elif yr < 2020:
            fedfunds_vals[i] = 2.15
        elif yr <= 2021:
            fedfunds_vals[i] = 0.08
        elif yr == 2022:
            fedfunds_vals[i] = 0.1 + 0.35 * d.month
        else:
            fedfunds_vals[i] = 5.33
    fedfunds_vals = np.clip(np.round(fedfunds_vals, 2), 0.05, 10.0)
    df_fedfunds = pd.DataFrame({"date": dates_monthly, "value": fedfunds_vals})

    # 5. 10-Year Treasury Rate (GS10) (%)
    # Correlated with Fed Funds + term premium
    gs10_vals = np.zeros(n_months)
    for i, d in enumerate(dates_monthly):
        yr = d.year
        if yr < 2000:
            gs10_vals[i] = 6.5 - 0.1 * (yr - 1990) + 0.3 * np.sin(i * 0.1)
        elif yr < 2008:
            gs10_vals[i] = 4.8 + 0.4 * np.sin(i * 0.1)
        elif yr < 2020:
            gs10_vals[i] = 2.5 + 0.5 * np.sin(i * 0.15)
        elif yr == 2020:
            gs10_vals[i] = 0.89
        elif yr == 2021:
            gs10_vals[i] = 1.45
        elif yr == 2022:
            gs10_vals[i] = 2.95
        else:
            gs10_vals[i] = 4.25 + 0.2 * np.sin(i * 0.1)
    gs10_vals = np.clip(np.round(gs10_vals, 2), 0.5, 9.0)
    df_gs10 = pd.DataFrame({"date": dates_monthly, "value": gs10_vals})

    return {
        "GDPC1": df_gdp,
        "CPIAUCSL": df_cpi,
        "UNRATE": df_unrate,
        "FEDFUNDS": df_fedfunds,
        "GS10": df_gs10,
    }
