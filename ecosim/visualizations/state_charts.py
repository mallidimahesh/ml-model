"""Interactive Plotly visualizations for Indian State-Level Economic Intelligence in EcoSim.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Theme palette matching EcoSim institutional styling
STATE_COLORS = {
    "navy": "#0F172A",
    "blue": "#2563EB",
    "teal": "#0D9488",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "coral": "#E11D48",
    "green": "#10B981",
    "amber": "#D97706",
    "card_bg": "#FFFFFF",
    "plot_bg": "#FFFFFF",
    "grid": "#F1F5F9",
    "border": "#E2E8F0",
}


def plot_state_ranking_barchart(
    df: pd.DataFrame,
    indicator_col: str,
    indicator_name: str,
    unit: str,
    source_name: str,
    ref_year_col: str = "",
    top_n: int | None = None,
    ascending: bool = True,
    color_scale: str = "Blues",
) -> go.Figure:
    """Horizontal bar chart ranking Indian states by economic indicator."""
    clean = df.dropna(subset=[indicator_col]).copy()
    if clean.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No state observations available for this indicator.",
            showarrow=False,
            font=dict(size=14, color="#64748B"),
        )
        fig.update_layout(height=350, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF")
        return fig

    # Sort values
    clean = clean.sort_values(indicator_col, ascending=ascending)
    if top_n and len(clean) > top_n:
        clean = clean.iloc[-top_n:]

    # Tooltip reference years
    if ref_year_col and ref_year_col in clean.columns:
        ref_text = clean[ref_year_col].fillna("Latest").astype(str)
    else:
        ref_text = ["Latest Observed"] * len(clean)

    # Hover template
    hover_tpl = (
        "<b>%{y}</b><br>"
        f"{indicator_name}: %{{x:,.2f}} {unit}<br>"
        "Reference Period: %{customdata[0]}<br>"
        f"Official Source: {source_name}<extra></extra>"
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=clean["state"],
            x=clean[indicator_col],
            orientation="h",
            marker=dict(
                color=clean[indicator_col],
                colorscale=color_scale,
                showscale=False,
                line=dict(width=0.5, color="#CBD5E1"),
            ),
            text=[f"{v:,.1f} {unit}" if v >= 100 else f"{v:.2f}{unit}" for v in clean[indicator_col]],
            textposition="auto",
            customdata=np.stack([ref_text], axis=-1),
            hovertemplate=hover_tpl,
        )
    )

    chart_height = max(420, len(clean) * 22)
    fig.update_layout(
        title=f"<b>State Ranking: {indicator_name} ({unit})</b>",
        xaxis_title=f"{indicator_name} ({unit})",
        yaxis_title="",
        template="plotly_white",
        paper_bgcolor=STATE_COLORS["card_bg"],
        plot_bgcolor=STATE_COLORS["plot_bg"],
        height=chart_height,
        margin=dict(l=140, r=40, t=50, b=45),
    )
    fig.update_xaxes(gridcolor=STATE_COLORS["grid"])
    fig.update_yaxes(gridcolor=STATE_COLORS["grid"], tickfont=dict(size=11, color="#334155"))
    return fig


def plot_state_historical_trends(
    df_trends: pd.DataFrame,
    states_selected: list[str],
    metric_col: str,
    metric_name: str,
    unit: str,
    source_name: str,
) -> go.Figure:
    """Multi-line time series chart comparing selected states over historical observation years."""
    fig = go.Figure()

    palette = [
        "#2563EB", "#0D9488", "#EA580C", "#7C3AED", "#E11D48",
        "#10B981", "#D97706", "#475569", "#6366F1", "#EC4899",
    ]

    has_data = False
    for i, sname in enumerate(states_selected):
        s_df = df_trends[df_trends["state"] == sname].dropna(subset=[metric_col]).sort_values("year")
        if not s_df.empty:
            has_data = True
            color = palette[i % len(palette)]
            fig.add_trace(
                go.Scatter(
                    x=s_df["year"],
                    y=s_df[metric_col],
                    mode="lines+markers",
                    name=sname,
                    line=dict(width=2.5, color=color),
                    marker=dict(size=6, color=color),
                    hovertemplate=(
                        f"<b>{sname}</b><br>"
                        f"Year: %{{x}}<br>"
                        f"{metric_name}: %{{y:,.2f}} {unit}<br>"
                        f"Source: {source_name}<extra></extra>"
                    ),
                )
            )

    if not has_data:
        fig.add_annotation(
            text=f"No historical time-series data available for selected states on {metric_name}.",
            showarrow=False,
            font=dict(size=13, color="#64748B"),
        )

    fig.update_layout(
        title=f"<b>Historical State Comparison: {metric_name} ({unit})</b>",
        xaxis_title="Financial Year / Survey Round",
        yaxis_title=f"{metric_name} ({unit})",
        template="plotly_white",
        paper_bgcolor=STATE_COLORS["card_bg"],
        plot_bgcolor=STATE_COLORS["plot_bg"],
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
        margin=dict(l=45, r=25, t=55, b=50),
    )
    fig.update_xaxes(gridcolor=STATE_COLORS["grid"])
    fig.update_yaxes(gridcolor=STATE_COLORS["grid"])
    return fig


def plot_stress_index_breakdown(
    df_ranked: pd.DataFrame,
    detailed_results: list[Any],
    state_to_inspect: str,
) -> go.Figure:
    """Waterfall or horizontal contribution bar chart of stress components for a state."""
    # Find matching result
    res = next((r for r in detailed_results if r.state == state_to_inspect), None)
    fig = go.Figure()

    if res is None or not res.is_eligible_for_ranking:
        fig.add_annotation(
            text=f"Insufficient data coverage to decompose stress index for {state_to_inspect}.",
            showarrow=False,
            font=dict(size=13, color="#64748B"),
        )
        fig.update_layout(height=320, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF")
        return fig

    labels = []
    contributions = []
    raw_texts = []

    comp_name_map = {
        "debt_gsdp_pct": "Debt Burden (Debt/GSDP)",
        "plfs_ur": "Labour Market Slack (UR)",
        "cpi_inflation_yoy": "Purchasing Power (CPI)",
        "gfd_gsdp_pct": "Fiscal Deficit (GFD/GSDP)",
        "real_growth_yoy": "Growth Headwind (Inverted)",
    }

    for k, name in comp_name_map.items():
        c_val = res.component_contributions.get(k)
        r_val = res.component_raw_values.get(k)
        if c_val is not None:
            labels.append(name)
            contributions.append(c_val)
            raw_texts.append(f"{c_val:.1f} pts (Raw: {r_val:.2f})")

    fig.add_trace(
        go.Bar(
            y=labels,
            x=contributions,
            orientation="h",
            marker=dict(
                color=["#E11D48", "#EA580C", "#D97706", "#2563EB", "#7C3AED"][:len(labels)],
                line=dict(width=0.5, color="#CBD5E1"),
            ),
            text=raw_texts,
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Stress Contribution: %{x:.2f} pts<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"<b>Component Stress Contribution Decomposition — {state_to_inspect} (Total Score: {res.stress_score:.1f}/100)</b>",
        xaxis_title="Weighted Contribution to Total Stress Score (Points)",
        yaxis_title="",
        template="plotly_white",
        paper_bgcolor=STATE_COLORS["card_bg"],
        plot_bgcolor=STATE_COLORS["plot_bg"],
        height=320,
        margin=dict(l=170, r=30, t=50, b=40),
    )
    fig.update_xaxes(gridcolor=STATE_COLORS["grid"])
    fig.update_yaxes(gridcolor=STATE_COLORS["grid"])
    return fig


def plot_stress_quadrant(df_ranked: pd.DataFrame) -> go.Figure:
    """Scatter quadrant relating Fiscal Debt Burden (% of GSDP) vs PLFS Unemployment Rate (%)."""
    clean = df_ranked.dropna(subset=["debt_gsdp_pct", "plfs_ur", "stress_score"]).copy()
    fig = go.Figure()

    if clean.empty:
        fig.add_annotation(text="Insufficient data for quadrant mapping.", showarrow=False)
        return fig

    # Median crosshairs
    med_debt = clean["debt_gsdp_pct"].median()
    med_ur = clean["plfs_ur"].median()

    tier_colors = {
        "High Relative Stress": "#E11D48",
        "Elevated Vulnerability": "#EA580C",
        "Moderate Vulnerability": "#D97706",
        "Low Economic Vulnerability": "#10B981",
    }

    for tier, grp in clean.groupby("stress_tier"):
        fig.add_trace(
            go.Scatter(
                x=grp["debt_gsdp_pct"],
                y=grp["plfs_ur"],
                mode="markers+text",
                name=tier,
                text=grp["state_code"],
                textposition="top right",
                marker=dict(
                    size=11,
                    color=tier_colors.get(tier, "#2563EB"),
                    line=dict(width=1, color="#FFFFFF"),
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Debt / GSDP: %{x:.1f}%<br>"
                    "Unemployment Rate: %{y:.1f}%<br>"
                    "Stress Score: %{customdata[1]:.1f}<extra></extra>"
                ),
                customdata=grp[["state", "stress_score"]].values,
            )
        )

    # Reference median lines
    fig.add_vline(x=med_debt, line_dash="dash", line_color="#94A3B8", annotation_text=f"Median Debt ({med_debt:.1f}%)", annotation_position="top left")
    fig.add_hline(y=med_ur, line_dash="dash", line_color="#94A3B8", annotation_text=f"Median UR ({med_ur:.1f}%)", annotation_position="bottom right")

    fig.update_layout(
        title="<b>State Vulnerability Matrix: Fiscal Debt Burden vs. Unemployment Slack</b>",
        xaxis_title="State Debt as % of GSDP (RBI State Finances)",
        yaxis_title="Unemployment Rate % (MoSPI PLFS Usual Status 15+)",
        template="plotly_white",
        paper_bgcolor=STATE_COLORS["card_bg"],
        plot_bgcolor=STATE_COLORS["plot_bg"],
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0),
        margin=dict(l=45, r=35, t=55, b=50),
    )
    fig.update_xaxes(gridcolor=STATE_COLORS["grid"])
    fig.update_yaxes(gridcolor=STATE_COLORS["grid"])
    return fig
