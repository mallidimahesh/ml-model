"""Plotly Interactive Visualizations for EcoSim.

Professional institutional financial terminal charts with restrained colors,
crisp typography, subtle gridlines, and clean informative tooltips.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ecosim.models.regime_analytics import US_NBER_RECESSIONS, load_india_quarterly_phillips_dataset

# Palette: Modern Premium Economic Intelligence
COLORS = {
    "navy": "#0F172A",       # Core primary dark series
    "orange": "#FF5200",     # Vibrant signature warm accent (Swiggy / Stripe inspired)
    "blue": "#2563EB",       # Secondary monetary series
    "teal": "#0D9488",       # Spread / Treasury
    "amber": "#F59E0B",      # Warnings / LM curves
    "crimson": "#EF4444",    # Inflation / Forecast deviations
    "green": "#10B981",      # Labor / Multiplier expansion
    "purple": "#8B5CF6",     # Derived / Marker diamonds
    "slate": "#64748B",      # Muted reference lines
    "dark_slate": "#0F172A",  # Text and primary headers
    "grid": "#F1F5F9",       # Clean light gridlines
    "card_bg": "#FFFFFF",    # Card backgrounds
    "plot_bg": "#FFFFFF",    # Plot area
}


def apply_terminal_theme(
    fig: go.Figure,
    height: int = 460,
    title: str | None = None,
    show_legend: bool = True,
) -> go.Figure:
    """Apply modern premium web aesthetic to a Plotly figure."""
    layout_update = dict(
        height=height,
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            size=11.5,
            color=COLORS["dark_slate"],
        ),
        margin=dict(l=45, r=25, t=55 if title else 35, b=45),
        hoverlabel=dict(
            bgcolor=COLORS["dark_slate"],
            font_size=11.5,
            font_family="Inter, -apple-system, sans-serif",
            font_color="#FFFFFF",
            bordercolor=COLORS["dark_slate"],
        ),
    )
    if title:
        layout_update["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(size=13.5, color=COLORS["dark_slate"], family="Inter, sans-serif"),
            x=0.01,
            xanchor="left",
            y=0.98,
        )
    if show_legend:
        layout_update["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="left",
            x=0.0,
            font=dict(size=11, color=COLORS["slate"]),
        )
    fig.update_layout(**layout_update)
    fig.update_xaxes(
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
        tickfont=dict(size=11, color=COLORS["slate"]),
    )
    fig.update_yaxes(
        gridcolor=COLORS["grid"],
        zerolinecolor=COLORS["grid"],
        tickfont=dict(size=11, color=COLORS["slate"]),
    )
    return fig


def add_nber_recession_bands(
    fig: go.Figure,
    df: pd.DataFrame,
    rows: list[int] | None = None,
    opacity: float = 0.22,
) -> go.Figure:
    """Add shaded vertical rectangle bands for US NBER recessions overlapping df."""
    if df.empty or "date" not in df.columns:
        return fig
    min_date = pd.to_datetime(df["date"].min())
    max_date = pd.to_datetime(df["date"].max())

    for rec in US_NBER_RECESSIONS:
        r_start = pd.to_datetime(rec["start"])
        r_end = pd.to_datetime(rec["end"])
        if r_end < min_date or r_start > max_date:
            continue
        x0 = max(r_start, min_date)
        x1 = min(r_end, max_date)
        if rows:
            for r in rows:
                fig.add_vrect(
                    x0=x0,
                    x1=x1,
                    fillcolor="#CBD5E1",
                    opacity=opacity,
                    line_width=0,
                    layer="below",
                    row=r,
                    col=1,
                )
        else:
            fig.add_vrect(
                x0=x0,
                x1=x1,
                fillcolor="#CBD5E1",
                opacity=opacity,
                line_width=0,
                layer="below",
            )
    return fig


def plot_macro_overview(df: pd.DataFrame) -> go.Figure:
    """Create a 3-panel synchronized time-series overview of US macroeconomic indicators with NBER recession bands."""
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "Output & Prices: Real GDP (₹B) and Consumer Price Index (CPI-U)",
            "Labor Market & Inflation: Civilian Unemployment (%) vs. YoY Inflation (%)",
            "Interest Rates & Term Structure: Effective Fed Funds Rate (%) vs. 10Y Treasury (%)",
        ),
    )

    # Panel 1: Real GDP & CPI
    if "GDPC1" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["GDPC1"], name="Real GDP (₹B Chained)",
                line=dict(color=COLORS["navy"], width=2),
                hovertemplate="Real GDP: ₹%{y:,.0f}B<extra></extra>",
            ),
            row=1, col=1,
        )
    if "CPIAUCSL" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["CPIAUCSL"], name="CPI-U (Index 1982-84=100)",
                line=dict(color=COLORS["amber"], width=1.5, dash="dot"),
                hovertemplate="CPI-U: %{y:.1f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # Panel 2: Unemployment & YoY Inflation
    if "UNRATE" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["UNRATE"], name="Unemployment Rate (%)",
                line=dict(color=COLORS["green"], width=2),
                hovertemplate="Unemployment: %{y:.1f}%<extra></extra>",
            ),
            row=2, col=1,
        )
    if "inflation_yoy" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["inflation_yoy"], name="YoY Inflation Rate (%)",
                line=dict(color=COLORS["crimson"], width=2),
                hovertemplate="YoY Inflation: %{y:.2f}%<extra></extra>",
            ),
            row=2, col=1,
        )

    # Panel 3: Interest Rates
    if "FEDFUNDS" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["FEDFUNDS"], name="Federal Funds Effective Rate (%)",
                line=dict(color=COLORS["blue"], width=2),
                hovertemplate="Fed Funds: %{y:.2f}%<extra></extra>",
            ),
            row=3, col=1,
        )
    if "GS10" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"], y=df["GS10"], name="10-Year Treasury Yield (%)",
                line=dict(color=COLORS["teal"], width=2),
                hovertemplate="10Y Treasury: %{y:.2f}%<extra></extra>",
            ),
            row=3, col=1,
        )

    # Add shaded NBER recession bands across all 3 panels
    add_nber_recession_bands(fig, df, rows=[1, 2, 3], opacity=0.25)

    fig.update_layout(
        height=720,
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
        margin=dict(l=45, r=25, t=40, b=45),
    )
    for r in [1, 2, 3]:
        fig.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], row=r, col=1)
        fig.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], row=r, col=1)

    return fig


def plot_multi_series_selector(
    df: pd.DataFrame,
    selected_indicators: list[str],
) -> go.Figure:
    """Render interactive multi-indicator comparison chart with dual axis support."""
    fig = go.Figure()

    meta = {
        "inflation_yoy": {"name": "YoY Inflation Rate (%)", "color": COLORS["orange"], "dash": "solid", "axis": "y"},
        "UNRATE": {"name": "Civilian Unemployment Rate (%)", "color": COLORS["blue"], "dash": "solid", "axis": "y"},
        "FEDFUNDS": {"name": "Federal Funds Rate (%)", "color": COLORS["green"], "dash": "solid", "axis": "y"},
        "GS10": {"name": "10-Year Treasury Yield (%)", "color": COLORS["teal"], "dash": "solid", "axis": "y"},
        "misery_index": {"name": "Misery Index (Inf + Unemp)", "color": COLORS["purple"], "dash": "dash", "axis": "y"},
        "real_interest_rate": {"name": "Approx. Real Rate (FedFunds - Inf)", "color": COLORS["slate"], "dash": "dashdot", "axis": "y"},
        "gdp_growth_yoy": {"name": "Real GDP Growth YoY (%)", "color": COLORS["navy"], "dash": "solid", "axis": "y"},
        "GDPC1": {"name": "Real GDP Level (₹B Chained)", "color": COLORS["navy"], "dash": "solid", "axis": "y2"},
    }

    has_y2 = False
    for ind in selected_indicators:
        if ind in df.columns and ind in meta:
            m = meta[ind]
            is_secondary = m["axis"] == "y2"
            if is_secondary:
                has_y2 = True
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[ind],
                    name=m["name"],
                    yaxis="y2" if is_secondary else "y",
                    line=dict(color=m["color"], width=2.2, dash=m["dash"]),
                    hovertemplate=f"{m['name']}: %{{y:.2f}}<extra></extra>",
                )
            )

    layout_update = dict(
        height=450,
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        hovermode="x unified",
        xaxis=dict(title="Observation Date", gridcolor=COLORS["grid"]),
        yaxis=dict(title="Rate / Index Value (%)", gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
        margin=dict(l=45, r=45 if has_y2 else 25, t=30, b=45),
    )
    if has_y2:
        layout_update["yaxis2"] = dict(
            title="Real GDP (₹ Billions)",
            overlaying="y",
            side="right",
            gridcolor=COLORS["grid"],
        )

    fig.update_layout(**layout_update)
    return fig


def plot_phillips_curve(
    df: pd.DataFrame,
    country: str = "USA",
    rolling_window: int = 48,
) -> tuple[go.Figure, float, float, float, float, int, pd.Timestamp | None, pd.Timestamp | None, str]:
    """Generate Phillips Curve scatter with fitted linear regression & rolling R-squared.

    Args:
        df: DataFrame containing macroeconomic series.
        country: "USA" (FRED UNRATE vs CPIAUCSL YoY) or "India" (MoSPI PLFS Urban vs CPI YoY).
        rolling_window: Window size for rolling correlation/R² (months for US, quarters for India).

    Returns:
        tuple: (fig, slope, intercept, r2, correlation, sample_size, start_date, end_date, equation_str)
    """
    if country == "India":
        if "unrate" in df.columns and "cpi_yoy" in df.columns:
            clean = df.dropna(subset=["unrate", "cpi_yoy"]).copy()
            x_col = "unrate"
            y_col = "cpi_yoy"
        else:
            clean = load_india_quarterly_phillips_dataset()
            x_col = "unrate"
            y_col = "cpi_yoy"
        x_title = "Urban Unemployment Rate (% — MoSPI PLFS CWS)"
        y_title = "CPI Combined Inflation Rate (% YoY — RBI DBIE)"
        freq_label = "Quarterly Observations"
        # Minimum window for quarterly data is typically 8-12 quarters
        effective_window = min(rolling_window, 8) if rolling_window > 16 else max(4, rolling_window)
    else:
        clean = df.dropna(subset=["UNRATE", "inflation_yoy"]).copy()
        x_col = "UNRATE"
        y_col = "inflation_yoy"
        x_title = "Civilian Unemployment Rate (% — FRED UNRATE)"
        y_title = "CPI-U Inflation Rate (% YoY — FRED CPIAUCSL)"
        freq_label = "Monthly Observations"
        effective_window = rolling_window

    if len(clean) < 6:
        fig = go.Figure()
        return (
            apply_terminal_theme(fig, title=f"Insufficient Data for Phillips Curve ({country})"),
            0.0, 0.0, 0.0, 0.0, 0, None, None, "π = 0.00 + (0.00) × U"
        )

    clean["date"] = pd.to_datetime(clean["date"])
    clean = clean.sort_values("date").reset_index(drop=True)

    x = clean[x_col].values.astype(float)
    y = clean[y_col].values.astype(float)

    # Fit linear regression line: y = slope * x + intercept
    slope, intercept = np.polyfit(x, y, 1)
    correlation = float(np.corrcoef(x, y)[0, 1])
    overall_r2 = float(correlation ** 2)

    # Line coordinates
    x_line = np.linspace(x.min(), x.max(), 50)
    y_line = slope * x_line + intercept

    eq_str = f"π̂ = {intercept:.2f} + ({slope:.2f}) × u"

    # Rolling R-squared
    has_sufficient_rolling = len(clean) >= effective_window
    if has_sufficient_rolling:
        clean["rolling_corr"] = clean[x_col].rolling(effective_window).corr(clean[y_col])
        clean["rolling_r2"] = clean["rolling_corr"] ** 2
    else:
        clean["rolling_r2"] = np.nan

    period_unit = "Quarter" if country == "India" else "Month"
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        row_heights=[0.68, 0.32],
        vertical_spacing=0.14,
        subplot_titles=(
            f"Phillips Scatter: {country} Inflation vs Unemployment (OLS: {eq_str}, R² = {overall_r2:.3f}, N = {len(clean)})",
            f"Rolling {effective_window}-{period_unit} R-Squared (Time Evolution of Phillips Trade-Off)"
            if has_sufficient_rolling else f"Rolling R² (Requires at least {effective_window} consecutive {period_unit}s; available: {len(clean)})",
        ),
    )

    # Subplot 1: Scatter & Regression Line
    fig.add_trace(
        go.Scatter(
            x=clean[x_col],
            y=clean[y_col],
            mode="markers",
            name=freq_label,
            marker=dict(
                size=7,
                color=clean["date"].dt.year,
                colorscale="Blues",
                showscale=True,
                colorbar=dict(title="Year", x=1.02, y=0.75, len=0.45),
                line=dict(width=0.6, color=COLORS["navy"]),
            ),
            text=clean["date"].dt.strftime("%b %Y"),
            hovertemplate="Period: %{text}<br>Unemployment: %{x:.1f}%<br>YoY Inflation: %{y:.2f}%<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name=f"Fitted OLS: {eq_str}",
            line=dict(color=COLORS["crimson"], width=2.5, dash="dash"),
        ),
        row=1, col=1,
    )

    # Subplot 2: Rolling R-squared
    if has_sufficient_rolling:
        fig.add_trace(
            go.Scatter(
                x=clean["date"],
                y=clean["rolling_r2"],
                mode="lines",
                name=f"Rolling {effective_window}{period_unit[0]} R²",
                line=dict(color=COLORS["teal"], width=2),
                fill="tozeroy",
                fillcolor="rgba(15, 118, 110, 0.12)",
                hovertemplate="Date: %{x|%b %Y}<br>Rolling R²: %{y:.3f}<extra></extra>",
            ),
            row=2, col=1,
        )
    else:
        fig.add_annotation(
            text=f"Sample size ({len(clean)} {period_unit.lower()}s) is smaller than requested rolling window ({effective_window} {period_unit.lower()}s).",
            xref="x2", yref="y2",
            x=clean["date"].iloc[len(clean)//2], y=0.5,
            showarrow=False,
            font=dict(size=12, color=COLORS["slate"]),
            row=2, col=1,
        )

    fig.update_xaxes(title_text=x_title, row=1, col=1, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text=y_title, row=1, col=1, gridcolor=COLORS["grid"])
    fig.update_xaxes(title_text="Observation Date", row=2, col=1, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="Rolling R²", row=2, col=1, gridcolor=COLORS["grid"], range=[0, 1])

    fig.update_layout(
        height=680,
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=-0.14, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=45, b=45),
    )
    return (
        fig,
        float(slope),
        float(intercept),
        float(overall_r2),
        float(correlation),
        int(len(clean)),
        clean["date"].iloc[0],
        clean["date"].iloc[-1],
        eq_str,
    )


def plot_actual_vs_predicted(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    split_date: pd.Timestamp,
    mae: float,
    rmse: float,
    r2: float,
    next_forecast: float | None = None,
    next_date: pd.Timestamp | None = None,
) -> go.Figure:
    """Create Actual vs Predicted Inflation time series with chronological holdout split and forecast point."""
    fig = go.Figure()

    # Training fit (in-sample)
    fig.add_trace(
        go.Scatter(
            x=train_df["date"],
            y=train_df["actual"],
            mode="lines",
            name="In-Sample Actual (π)",
            line=dict(color=COLORS["slate"], width=1.5),
            hovertemplate="Train Actual: %{y:.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=train_df["date"],
            y=train_df["predicted"],
            mode="lines",
            name="In-Sample Ridge Fit",
            line=dict(color="#94A3B8", width=1.2, dash="dot"),
            hovertemplate="Ridge In-Sample: %{y:.2f}%<extra></extra>",
        )
    )

    # Holdout test set (out-of-sample)
    fig.add_trace(
        go.Scatter(
            x=test_df["date"],
            y=test_df["actual"],
            mode="lines",
            name="Holdout Actual (Empirical Ground Truth)",
            line=dict(color=COLORS["navy"], width=2.5),
            hovertemplate="Test Actual: %{y:.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=test_df["date"],
            y=test_df["predicted"],
            mode="lines",
            name="Ridge Out-of-Sample Forecast",
            line=dict(color=COLORS["crimson"], width=2.5, dash="dash"),
            hovertemplate="Ridge Forecast: %{y:.2f}%<extra></extra>",
        )
    )

    # Upcoming out-of-sample forecast point if available
    if next_forecast is not None and next_date is not None:
        fig.add_trace(
            go.Scatter(
                x=[next_date],
                y=[next_forecast],
                mode="markers+text",
                name="Upcoming Next-Quarter Forecast",
                marker=dict(color=COLORS["purple"], size=11, symbol="diamond"),
                text=[f" {next_forecast:.2f}%"],
                textposition="top center",
                hovertemplate=f"Forecast Horizon: %{{x|%b %Y}}<br>Projected YoY Inflation: {next_forecast:.2f}%<extra></extra>",
            )
        )

    # Vertical split boundary
    fig.add_vline(
        x=split_date,
        line_width=1.5,
        line_dash="dash",
        line_color=COLORS["dark_slate"],
        annotation_text="Chronological Holdout Boundary",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["dark_slate"]),
    )

    fig.update_layout(
        title=f"<b>Next-Quarter YoY Inflation: Out-of-Sample Evaluation (MAE: {mae:.2f}%, RMSE: {rmse:.2f}%, R²: {r2:.3f})</b>",
        xaxis_title="Quarterly Observation Date",
        yaxis_title="Next-Quarter YoY Inflation Rate (%)",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=480,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_feature_coefficients(coef_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart showing standardized Ridge coefficients (relative feature weights)."""
    fig = go.Figure()

    df_sorted = coef_df.sort_values("Standardized_Coefficient", ascending=True).copy()
    bar_colors = [COLORS["navy"] if c >= 0 else COLORS["crimson"] for c in df_sorted["Standardized_Coefficient"]]

    fig.add_trace(
        go.Bar(
            y=df_sorted["Feature"],
            x=df_sorted["Standardized_Coefficient"],
            orientation="h",
            marker=dict(color=bar_colors),
            text=[f"{v:+.3f}" for v in df_sorted["Standardized_Coefficient"]],
            textposition="auto",
            hovertemplate="%{y}: %{x:+.4f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Standardized Ridge Regression Weights (Normalized Feature Sensitivity)</b>",
        xaxis_title="Standardized Coefficient Magnitude",
        yaxis_title="Lagged Predictor Variable",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=320,
        margin=dict(l=140, r=25, t=45, b=35),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"], zeroline=True, zerolinecolor=COLORS["dark_slate"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_is_lm_curves(
    curve_df: pd.DataFrame,
    y_base: float,
    r_base: float,
    y_new: float,
    r_new: float,
) -> go.Figure:
    """Render interactive IS and LM curves under baseline and policy shocks."""
    fig = go.Figure()

    # IS Baseline and Policy
    fig.add_trace(
        go.Scatter(
            x=curve_df["Y"], y=curve_df["IS_Baseline"],
            name="IS (Baseline Goods Market Equilibrium)",
            line=dict(color=COLORS["navy"], width=2.5),
            hovertemplate="IS Baseline: (Y=%{x:.0f}, r=%{y:.2f}%)<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=curve_df["Y"], y=curve_df["IS_Policy"],
            name="IS' (Policy Equilibrium)",
            line=dict(color=COLORS["navy"], width=2, dash="dash"),
            hovertemplate="IS Policy: (Y=%{x:.0f}, r=%{y:.2f}%)<extra></extra>",
        )
    )

    # LM Baseline and Policy
    fig.add_trace(
        go.Scatter(
            x=curve_df["Y"], y=curve_df["LM_Baseline"],
            name="LM (Baseline Money Market Equilibrium)",
            line=dict(color=COLORS["amber"], width=2.5),
            hovertemplate="LM Baseline: (Y=%{x:.0f}, r=%{y:.2f}%)<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=curve_df["Y"], y=curve_df["LM_Policy"],
            name="LM' (Policy Equilibrium)",
            line=dict(color=COLORS["amber"], width=2, dash="dash"),
            hovertemplate="LM Policy: (Y=%{x:.0f}, r=%{y:.2f}%)<extra></extra>",
        )
    )

    # Equilibrium Markers
    fig.add_trace(
        go.Scatter(
            x=[y_base], y=[r_base],
            mode="markers+text",
            name="Initial Equilibrium E₀",
            marker=dict(color=COLORS["dark_slate"], size=10, symbol="circle"),
            text=[f" E₀ ({y_base:.0f}, {r_base:.2f}%)"],
            textposition="top center",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[y_new], y=[r_new],
            mode="markers+text",
            name="Shocked Equilibrium E₁",
            marker=dict(color=COLORS["crimson"], size=12, symbol="star"),
            text=[f" E₁ ({y_new:.0f}, {r_new:.2f}%)"],
            textposition="bottom center",
        )
    )

    fig.update_layout(
        title="<b>IS–LM Simultaneous Goods & Money Market Equilibrium Shift</b>",
        xaxis_title="National Output / Aggregate Income (Y)",
        yaxis_title="Interest Rate (r, %)",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_keynesian_rounds(rounds_df: pd.DataFrame) -> go.Figure:
    """Plot Keynesian expenditure expansion rounds with Indian Rupees (₹B)."""
    fig = go.Figure()
    y_col = "Round Addition (₹B)" if "Round Addition (₹B)" in rounds_df.columns else "Round Addition ($B)"
    cum_col = "Cumulative Output (₹B)" if "Cumulative Output (₹B)" in rounds_df.columns else "Cumulative Output ($B)"

    fig.add_trace(
        go.Bar(
            x=rounds_df["Round"].astype(str),
            y=rounds_df[y_col],
            name="Round Spending Injection (₹B)",
            marker=dict(color=COLORS["green"]),
            text=rounds_df[y_col].map("₹{:,.1f}B".format),
            textposition="auto",
            hovertemplate="Round %{x}: ₹%{y:,.1f}B<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=rounds_df["Round"].astype(str),
            y=rounds_df[cum_col],
            name="Cumulative Output Expansion (₹B)",
            mode="lines+markers",
            line=dict(color=COLORS["navy"], width=2.5),
            marker=dict(size=7, color=COLORS["navy"]),
            yaxis="y2",
            hovertemplate="Cumulative Output: ₹%{y:,.1f}B<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Keynesian Expenditure Rounds: Multiplier Progression (₹ Billions)</b>",
        xaxis_title="Sequential Consumption Round",
        yaxis_title="Round Spending Addition (₹B)",
        yaxis2=dict(
            title="Cumulative Output Expansion (₹B)",
            overlaying="y",
            side="right",
            gridcolor=COLORS["grid"],
        ),
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=45, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_world_bank_indicator(
    df: pd.DataFrame,
    country_name: str,
    indicator_name: str,
    units: str = "%",
) -> go.Figure:
    """Plot World Bank cross-country annual indicator series."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["value"],
            mode="lines+markers",
            name=f"{country_name} - {indicator_name}",
            line=dict(color=COLORS["navy"], width=2.2),
            marker=dict(size=6, color=COLORS["blue"]),
            hovertemplate="Year: %{x}<br>Value: %{y:.2f}" + units + "<extra></extra>",
        )
    )
    return apply_terminal_theme(
        fig,
        height=420,
        title=f"{country_name}: {indicator_name} (World Bank Open Data)",
    )


def plot_india_target_forecast(eval_result: Any) -> go.Figure:
    """Plots actual series, out-of-sample holdout test predictions, and next-period forecast."""
    fig = go.Figure()

    train_df = eval_result.df_train
    test_df = eval_result.df_test

    # 1. Historical Actuals (Training Partition)
    fig.add_trace(
        go.Scatter(
            x=train_df["date"],
            y=train_df["actual"],
            mode="lines+markers",
            name="In-Sample Actual",
            line=dict(color="#64748B", width=2),
            marker=dict(size=4, color="#64748B"),
            hovertemplate="Training Actual: %{y:.2f}" + eval_result.target_unit + " (%{x|%b %Y})<extra></extra>",
        )
    )

    # 2. Out-of-Sample Holdout Actuals
    fig.add_trace(
        go.Scatter(
            x=test_df["date"],
            y=test_df["actual"],
            mode="lines+markers",
            name="Holdout Test Actual",
            line=dict(color="#0F172A", width=3),
            marker=dict(size=6, color="#0F172A"),
            hovertemplate="Test Actual: %{y:.2f}" + eval_result.target_unit + " (%{x|%b %Y})<extra></extra>",
        )
    )

    # 3. Ridge Regression Out-of-Sample Predictions
    fig.add_trace(
        go.Scatter(
            x=test_df["date"],
            y=test_df["ridge_pred"],
            mode="lines+markers",
            name="Ridge Regression Predicted",
            line=dict(color="#EA580C", width=2.5, dash="dash"),
            marker=dict(size=6, symbol="diamond", color="#EA580C"),
            hovertemplate="Ridge Pred: %{y:.2f}" + eval_result.target_unit + " (%{x|%b %Y})<extra></extra>",
        )
    )

    # 4. Persistence Benchmark Predictions (y_{t+1} = y_t)
    fig.add_trace(
        go.Scatter(
            x=test_df["date"],
            y=test_df["persistence_pred"],
            mode="lines",
            name="Persistence Baseline (y_{t+1}=y_t)",
            line=dict(color="#94A3B8", width=1.8, dash="dot"),
            hovertemplate="Persistence Baseline: %{y:.2f}" + eval_result.target_unit + " (%{x|%b %Y})<extra></extra>",
        )
    )

    # 5. Next-Period Unseen Forecast Point
    next_date = eval_result.target_period_date
    next_val = eval_result.next_period_ridge_forecast
    fig.add_trace(
        go.Scatter(
            x=[next_date],
            y=[next_val],
            mode="markers+text",
            name=f"Next Forecast ({eval_result.target_period_label})",
            marker=dict(size=14, color="#E11D48", symbol="star", line=dict(width=2, color="#FFFFFF")),
            text=[f" {next_val:.2f}{eval_result.target_unit}"],
            textposition="top center",
            textfont=dict(color="#E11D48", size=12, family="Inter, sans-serif"),
            hovertemplate=(
                f"<b>Next Forecast ({eval_result.target_period_label})</b><br>"
                f"Value: %{{y:.2f}}{eval_result.target_unit}<extra></extra>"
            ),
        )
    )

    # Add vertical split boundary
    split_date = eval_result.split_date
    fig.add_vline(
        x=split_date,
        line_width=1.5,
        line_dash="dash",
        line_color="#CBD5E1",
        annotation_text="Holdout Evaluation Split",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#64748B"),
    )

    title_text = f"<b>{eval_result.target_name} — Historical & Out-of-Sample Evaluation</b>"
    fig.update_layout(
        title=title_text,
        xaxis_title="Timeline",
        yaxis_title=f"{eval_result.target_name} ({eval_result.target_unit})",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=-0.26, xanchor="left", x=0),
        margin=dict(l=45, r=30, t=55, b=55),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_india_model_comparison(eval_result: Any) -> go.Figure:
    """Grouped bar chart comparing Ridge Regression against Persistence Baseline."""
    metrics = ["MAE (Mean Absolute Error)", "RMSE (Root Mean Squared Error)"]
    ridge_vals = [eval_result.ridge_mae, eval_result.ridge_rmse]
    persist_vals = [eval_result.persistence_mae, eval_result.persistence_rmse]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=metrics,
            y=ridge_vals,
            name="Ridge Regression (L2)",
            marker=dict(color="#EA580C"),
            text=[f"{v:.2f}%" for v in ridge_vals],
            textposition="auto",
            hovertemplate="Ridge %{x}: %{y:.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=metrics,
            y=persist_vals,
            name="Persistence Benchmark (y_{t+1}=y_t)",
            marker=dict(color="#64748B"),
            text=[f"{v:.2f}%" for v in persist_vals],
            textposition="auto",
            hovertemplate="Persistence %{x}: %{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Holdout Test Error Comparison (Lower is Superior)</b>",
        yaxis_title="Error (% points)",
        barmode="group",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
        margin=dict(l=35, r=20, t=45, b=40),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_india_coefficients(eval_result: Any) -> go.Figure:
    """Horizontal bar chart showing standardized feature coefficients."""
    df_c = eval_result.coefficients.sort_values("Absolute_Weight", ascending=True)

    bar_colors = ["#10B981" if c > 0 else "#EF4444" for c in df_c["Standardized_Coefficient"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df_c["Feature_Name"],
            x=df_c["Standardized_Coefficient"],
            orientation="h",
            marker=dict(color=bar_colors),
            text=[f"{c:+.3f}" for c in df_c["Standardized_Coefficient"]],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Standardized Coefficient: %{x:+.3f}<extra></extra>",
        )
    )

    fig.add_vline(x=0, line_width=1, line_color="#0F172A")
    fig.update_layout(
        title="<b>Standardized Predictor Coefficients (Relative Feature Weight)</b>",
        xaxis_title="Standardized Ridge Coefficient (Impact on Target)",
        yaxis_title="",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=320,
        margin=dict(l=40, r=25, t=45, b=35),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_inflation_decomposition(
    decomp: dict[str, Any],
    title: str = "Classical CPI Inflation Decomposition (Trend, Seasonality & Residual)",
    units: str = "Percent YoY (%)",
) -> go.Figure:
    """Render a 4-panel mathematical decomposition of monthly CPI inflation."""
    if not decomp or "observed" not in decomp or "trend" not in decomp:
        fig = go.Figure()
        return apply_terminal_theme(fig, title="Decomposition Unavailable (Requires Contiguous Monthly Series)")

    dates = decomp["dates"]
    observed = decomp["observed"]
    trend = decomp["trend"]
    seasonal = decomp["seasonal"]
    residual = decomp["residual"]
    shares = decomp.get("variance_shares", {})
    t_share = shares.get("trend_share", 0.0)
    s_share = shares.get("seasonal_share", 0.0)
    r_share = shares.get("residual_share", 0.0)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            f"1. Observed Inflation Series ({units})",
            f"2. Long-Term Trend Component [2×12 Centered Moving Average] ({t_share:.1f}% Variance Share)",
            f"3. 12-Month Seasonal Component [Normalized Zero-Sum Annual Factor] ({s_share:.1f}% Variance Share)",
            f"4. Residual Irregular Component [Noise & Supply Shocks: Y − T − S] ({r_share:.1f}% Variance Share)",
        ),
    )

    # 1. Observed
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=observed,
            name="Observed",
            line=dict(color=COLORS["navy"], width=2),
            hovertemplate="Observed: %{y:.2f}%<extra></extra>",
        ),
        row=1, col=1,
    )

    # 2. Trend
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=trend,
            name="Trend (2×12 MA)",
            line=dict(color=COLORS["orange"], width=2.5),
            hovertemplate="Trend: %{y:.2f}%<extra></extra>",
        ),
        row=2, col=1,
    )

    # 3. Seasonal
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=seasonal,
            name="Seasonal Factor",
            line=dict(color=COLORS["teal"], width=2),
            fill="tozeroy",
            fillcolor="rgba(13, 148, 136, 0.12)",
            hovertemplate="Seasonal: %{y:+.2f}%<extra></extra>",
        ),
        row=3, col=1,
    )

    # 4. Residual
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=residual,
            name="Residual / Irregular",
            line=dict(color=COLORS["crimson"], width=1.5),
            mode="lines+markers",
            marker=dict(size=3.5, color=COLORS["crimson"]),
            hovertemplate="Residual: %{y:+.2f}%<extra></extra>",
        ),
        row=4, col=1,
    )

    fig.update_layout(
        title=f"<b>{title}</b>",
        height=820,
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.08, xanchor="center", x=0.5),
        margin=dict(l=45, r=25, t=55, b=40),
    )
    for r in range(1, 5):
        fig.update_xaxes(gridcolor=COLORS["grid"], row=r, col=1)
        fig.update_yaxes(gridcolor=COLORS["grid"], row=r, col=1)

    return fig


def plot_inflation_turning_points(
    df_cpi: pd.DataFrame,
    df_peaks: pd.DataFrame,
    df_troughs: pd.DataFrame,
    title: str = "Headline CPI Inflation & Historical Turning Points",
    date_col: str = "date",
    val_col: str = "inflation_yoy",
) -> go.Figure:
    """Render headline inflation with identified structural peaks and troughs."""
    fig = go.Figure()

    # Main time series line
    fig.add_trace(
        go.Scatter(
            x=df_cpi[date_col],
            y=df_cpi[val_col],
            mode="lines",
            name="CPI Inflation Rate (% YoY)",
            line=dict(color=COLORS["navy"], width=2.2),
            hovertemplate="Date: %{x|%b %Y}<br>Inflation: %{y:.2f}%<extra></extra>",
        )
    )

    # Local Peaks
    if not df_peaks.empty:
        peak_y = df_peaks["peak_inflation"] if "peak_inflation" in df_peaks.columns else df_peaks[val_col]
        fig.add_trace(
            go.Scatter(
                x=df_peaks[date_col],
                y=peak_y,
                mode="markers+text",
                name="Inflation Peaks (Local Highs)",
                marker=dict(symbol="triangle-up", size=11, color=COLORS["crimson"], line=dict(width=1, color="#7F1D1D")),
                text=[f"{v:.1f}%" for v in peak_y],
                textposition="top center",
                textfont=dict(size=10, color=COLORS["crimson"]),
                hovertemplate="Peak: %{x|%b %Y}<br>Rate: %{y:.2f}%<extra></extra>",
            )
        )

    # Local Troughs
    if not df_troughs.empty:
        trough_y = df_troughs["trough_inflation"] if "trough_inflation" in df_troughs.columns else df_troughs[val_col]
        fig.add_trace(
            go.Scatter(
                x=df_troughs[date_col],
                y=trough_y,
                mode="markers+text",
                name="Inflation Troughs (Local Lows)",
                marker=dict(symbol="triangle-down", size=11, color=COLORS["green"], line=dict(width=1, color="#065F46")),
                text=[f"{v:.1f}%" for v in trough_y],
                textposition="bottom center",
                textfont=dict(size=10, color=COLORS["green"]),
                hovertemplate="Trough: %{x|%b %Y}<br>Rate: %{y:.2f}%<extra></extra>",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", line_width=1)

    fig.update_layout(
        title=f"<b>{title}</b>",
        xaxis_title="Observation Date",
        yaxis_title="Inflation Rate (% YoY)",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=440,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_regime_comparison_bars(
    summary_df: pd.DataFrame,
    title: str = "Macroeconomic Indicators: Expansions vs. Recessions",
    is_india: bool = False,
) -> go.Figure:
    """Grouped horizontal bar chart comparing indicators across economic regimes."""
    if summary_df.empty:
        fig = go.Figure()
        return apply_terminal_theme(fig, title="Regime Comparison Unavailable")

    col_exp = "Trend Growth Mean" if is_india else "Expansion Mean"
    col_rec = "Slowdown Mean" if is_india else "Recession Mean"
    leg_exp = "Trend Growth" if is_india else "NBER Expansion"
    leg_rec = "Analytical Slowdown" if is_india else "NBER Recession"

    indicators = summary_df["Indicator"].tolist()
    exp_vals = pd.to_numeric(summary_df[col_exp], errors="coerce").fillna(0).tolist()
    rec_vals = pd.to_numeric(summary_df[col_rec], errors="coerce").fillna(0).tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=indicators,
            x=exp_vals,
            name=leg_exp,
            orientation="h",
            marker=dict(color=COLORS["teal"]),
            text=[f"{v:.2f}%" for v in exp_vals],
            textposition="auto",
            hovertemplate=f"<b>%{{y}}</b><br>{leg_exp}: %{{x:.2f}}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=indicators,
            x=rec_vals,
            name=leg_rec,
            orientation="h",
            marker=dict(color=COLORS["crimson"] if not is_india else COLORS["orange"]),
            text=[f"{v:.2f}%" for v in rec_vals],
            textposition="auto",
            hovertemplate=f"<b>%{{y}}</b><br>{leg_rec}: %{{x:.2f}}%<extra></extra>",
        )
    )

    fig.add_vline(x=0, line_width=1, line_color="#0F172A")
    fig.update_layout(
        title=f"<b>{title}</b>",
        xaxis_title="Regime Average Value (% / % YoY)",
        barmode="group",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_world_bank_multi_country(
    df_matrix: pd.DataFrame,
    indicator_name: str,
    units: str,
    common_years: list[int] | None = None,
) -> go.Figure:
    """Render multi-country historical time series comparison with common-year shading."""
    fig = go.Figure()

    if df_matrix.empty or "year" not in df_matrix.columns:
        return apply_terminal_theme(fig, title="No World Bank Data Available")

    palette = ["#2563EB", "#FF5200", "#0D9488", "#7C3AED", "#10B981", "#EF4444", "#F59E0B", "#0284C7", "#D97706", "#475569"]
    country_cols = [c for c in df_matrix.columns if c != "year"]

    for idx, c in enumerate(country_cols):
        color = palette[idx % len(palette)]
        fig.add_trace(
            go.Scatter(
                x=df_matrix["year"],
                y=df_matrix[c],
                mode="lines+markers",
                name=c,
                line=dict(color=color, width=2.2),
                marker=dict(size=4),
                hovertemplate=f"<b>{c}</b> (%{{x}}): %{{y:.2f}} {units}<extra></extra>",
            )
        )

    # Highlight common comparison interval if available
    if common_years and len(common_years) >= 2:
        fig.add_vrect(
            x0=min(common_years),
            x1=max(common_years),
            fillcolor="#F1F5F9",
            opacity=0.45,
            layer="below",
            line_width=1,
            line_dash="dot",
            line_color="#CBD5E1",
            annotation_text="Common Years",
            annotation_position="top left",
            annotation=dict(font_size=9, font_color="#64748B"),
        )

    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", line_width=1)

    fig.update_layout(
        title=f"<b>World Bank Cross-Country Comparison: {indicator_name}</b>",
        xaxis_title="Observation Year",
        yaxis_title=f"{indicator_name} ({units})",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=480,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"], dtick=2)
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


def plot_world_bank_league_table(
    df_ranked: pd.DataFrame,
    indicator_name: str,
    units: str,
) -> go.Figure:
    """Render horizontal ranked bar league table for cross-country comparison."""
    if df_ranked.empty or "value" not in df_ranked.columns:
        fig = go.Figure()
        return apply_terminal_theme(fig, title="League Table Unavailable")

    clean = df_ranked.dropna(subset=["value"]).copy()
    clean = clean.sort_values("value", ascending=True)

    colors = [COLORS["teal"] if v >= 0 else COLORS["crimson"] for v in clean["value"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=clean["country"],
            x=clean["value"],
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v:.2f}% ({int(y)})" if pd.notna(y) else f"{v:.2f}%" for v, y in zip(clean["value"], clean["observation_year"])],
            textposition="auto",
            hovertemplate="<b>%{y}</b>: %{x:.2f}%<extra></extra>",
        )
    )

    fig.add_vline(x=0, line_width=1, line_color="#0F172A")
    fig.update_layout(
        title=f"<b>Cross-Country League Table: {indicator_name} ({units})</b>",
        xaxis_title=f"{indicator_name} ({units})",
        yaxis_title="",
        template="plotly_white",
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["plot_bg"],
        height=380,
        margin=dict(l=45, r=25, t=50, b=35),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])
    return fig


