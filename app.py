"""EcoSim: The Economy, Explained.

A high-polish, production-grade macroeconomic intelligence web platform
integrating live FRED and World Bank indicators with regularized Ridge
forecasting and classical macroeconomic policy simulation engines.
"""

from __future__ import annotations

import os
import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from ecosim.config import (
    FRED_API_KEY,
    FRED_SERIES,
    WORLD_BANK_INDICATORS,
    DISCLAIMERS,
    INDIAN_MACRO_SERIES,
    INDIAN_STATE_SERIES,
    RBI_DBIE_BASE_URL,
    MOSPI_API_BASE_URL,
    MOSPI_API_TOKEN,
)
from ecosim.data.fred_client import FredClient
from ecosim.data.world_bank import WorldBankClient, SUPPORTED_COUNTRIES
from ecosim.data.data_processor import (
    harmonize_macro_series,
    calculate_derived_indicators,
    prepare_quarterly_forecasting_dataset,
)
from ecosim.data.india_data import IndiaDataClient, build_india_forecasting_datasets
from ecosim.data.india_state_data import IndiaStateDataClient, INDIAN_STATES_METADATA
from ecosim.models.ridge_model import MacroRidgeForecaster, FEATURE_METADATA
from ecosim.models.india_forecaster import IndiaMultiForecaster, TargetEvaluationResult
from ecosim.models.state_stress_index import (
    compute_state_economic_stress_index,
    StateStressResult,
    STRESS_COMPONENTS,
)
from ecosim.models.regime_analytics import (
    US_NBER_RECESSIONS,
    INDIA_SLOWDOWN_REGIMES,
    get_nber_recessions,
    get_india_slowdowns,
    classify_us_regimes,
    compute_us_regime_statistics,
    compute_india_slowdown_statistics,
    validate_monthly_continuity,
    calculate_mom_yoy_inflation,
    decompose_monthly_inflation_classical,
    detect_inflation_turning_points,
    load_india_quarterly_phillips_dataset,
)
from ecosim.simulators.keynesian import simulate_keynesian_multiplier
from ecosim.simulators.is_lm import simulate_is_lm
from ecosim.visualizations.charts import (
    plot_macro_overview,
    plot_multi_series_selector,
    plot_actual_vs_predicted,
    plot_feature_coefficients,
    plot_phillips_curve,
    plot_keynesian_rounds,
    plot_is_lm_curves,
    plot_world_bank_indicator,
    plot_india_target_forecast,
    plot_india_model_comparison,
    plot_india_coefficients,
    plot_inflation_decomposition,
    plot_inflation_turning_points,
    plot_regime_comparison_bars,
    plot_world_bank_multi_country,
    plot_world_bank_league_table,
    add_nber_recession_bands,
    apply_terminal_theme,
)
from ecosim.visualizations.state_charts import (
    plot_state_ranking_barchart,
    plot_state_historical_trends,
    plot_stress_index_breakdown,
    plot_stress_quadrant,
)

# Page configuration - Clean web application layout with collapsed sidebar by default
st.set_page_config(
    page_title="EcoSim — The Economy, Explained",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Premium Modern Web App Design System
st.markdown(
    """
    <style>
    /* Global Typography & Font Family */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #0F172A;
    }

    /* Soft Warm Neutral Page Background */
    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Main Container Padding & Max Width */
    .main .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
        max-width: 1380px !important;
    }

    /* Header Brand Styling */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        text-decoration: none !important;
        cursor: pointer;
    }
    .brand-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #FF5200 0%, #EA580C 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(255, 82, 0, 0.28);
    }
    .brand-title {
        font-size: 23px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .brand-pill {
        font-size: 11px;
        font-weight: 700;
        color: #FF5200;
        background: #FFF7ED;
        border: 1px solid #FFEDD5;
        padding: 3px 9px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Feed Status Pills */
    .badge-live-pill {
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
        font-size: 11.5px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.02em;
    }
    .badge-demo-pill {
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
        font-size: 11.5px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.02em;
    }
    .pulse-dot-live {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #16A34A;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.2);
    }
    .pulse-dot-demo {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #D97706;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.2);
    }

    /* -------------------------------------------------------------------------
       NEW HOMEPAGE HERO & FIVE LARGE COLOURFUL FEATURE CARDS
       ------------------------------------------------------------------------- */
    .home-welcome-header {
        text-align: center;
        margin: 14px 0 26px 0;
    }
    .home-welcome-eyebrow {
        font-size: 11.5px;
        font-weight: 700;
        color: #FF5200;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .home-welcome-title {
        font-size: 34px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .home-welcome-subtitle {
        font-size: 15px;
        color: #64748B;
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Clickable Feature Card Wrappers */
    .feature-card-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        margin-bottom: 8px;
    }
    .feature-card {
        border-radius: 18px;
        padding: 24px 26px;
        color: #0F172A;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 255px;
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.10);
    }

    /* Card 1: Soft Dimmed Blue */
    .card-blue {
        background: linear-gradient(145deg, #FFFFFF 0%, #F4F8FF 60%, #EBF3FF 100%);
        border: 1.5px solid #BFDBFE;
    }
    .card-blue:hover {
        border-color: #3B82F6;
        box-shadow: 0 14px 30px rgba(37, 99, 235, 0.12);
    }

    /* Card 2: Soft Dimmed Teal */
    .card-teal {
        background: linear-gradient(145deg, #FFFFFF 0%, #F2FBF9 60%, #E6F7F4 100%);
        border: 1.5px solid #99F6E4;
    }
    .card-teal:hover {
        border-color: #14B8A6;
        box-shadow: 0 14px 30px rgba(13, 148, 136, 0.12);
    }

    /* Card: Soft Dimmed Emerald (State Economic Intelligence) */
    .card-emerald {
        background: linear-gradient(145deg, #FFFFFF 0%, #F0FDF4 60%, #DCFCE7 100%);
        border: 1.5px solid #BBF7D0;
    }
    .card-emerald:hover {
        border-color: #16A34A;
        box-shadow: 0 14px 30px rgba(22, 163, 74, 0.12);
    }

    /* Card: Soft Dimmed Purple (Phillips Curve) */
    .card-purple {
        background: linear-gradient(145deg, #FFFFFF 0%, #FAF5FF 60%, #F3E8FF 100%);
        border: 1.5px solid #E9D5FF;
    }
    .card-purple:hover {
        border-color: #9333EA;
        box-shadow: 0 14px 30px rgba(147, 51, 234, 0.12);
    }

    /* Card 3: Soft Dimmed Indigo (India Macro Forecast) */
    .card-indigo {
        background: linear-gradient(145deg, #FFFFFF 0%, #F5F3FF 60%, #EDE9FE 100%);
        border: 1.5px solid #DDD6FE;
    }
    .card-indigo:hover {
        border-color: #7C3AED;
        box-shadow: 0 14px 30px rgba(124, 58, 237, 0.12);
    }

    /* Card 4: Soft Dimmed Orange */
    .card-orange {
        background: linear-gradient(145deg, #FFFFFF 0%, #FFF9F2 60%, #FFF1E3 100%);
        border: 1.5px solid #FED7AA;
    }
    .card-orange:hover {
        border-color: #F97316;
        box-shadow: 0 14px 30px rgba(234, 88, 12, 0.12);
    }

    /* Card 5: Soft Dimmed Coral */
    .card-coral {
        background: linear-gradient(145deg, #FFFFFF 0%, #FFF5F6 60%, #FFE9EC 100%);
        border: 1.5px solid #FECDD3;
    }
    .card-coral:hover {
        border-color: #F43F5E;
        box-shadow: 0 14px 30px rgba(220, 38, 38, 0.12);
    }

    /* Card Elements */
    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .card-icon-bubble {
        width: 46px;
        height: 46px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
    }
    .bubble-blue {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
    }
    .bubble-teal {
        background: #F0FDFA;
        border: 1px solid #99F6E4;
    }
    .bubble-emerald {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
    }
    .bubble-purple {
        background: #FAF5FF;
        border: 1px solid #E9D5FF;
    }
    .bubble-indigo {
        background: #F5F3FF;
        border: 1px solid #DDD6FE;
    }
    .bubble-orange {
        background: #FFF7ED;
        border: 1px solid #FED7AA;
    }
    .bubble-coral {
        background: #FFF1F2;
        border: 1px solid #FECDD3;
    }

    .card-pill-tag {
        font-size: 10.5px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .tag-blue {
        background: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .tag-teal {
        background: #F0FDFA;
        color: #0F766E;
        border: 1px solid #99F6E4;
    }
    .tag-emerald {
        background: #F0FDF4;
        color: #15803D;
        border: 1px solid #BBF7D0;
    }
    .tag-purple {
        background: #FAF5FF;
        color: #7E22CE;
        border: 1px solid #E9D5FF;
    }
    .tag-indigo {
        background: #F5F3FF;
        color: #6D28D9;
        border: 1px solid #DDD6FE;
    }
    .tag-orange {
        background: #FFF7ED;
        color: #C2410C;
        border: 1px solid #FED7AA;
    }
    .tag-coral {
        background: #FFF1F2;
        color: #BE123C;
        border: 1px solid #FECDD3;
    }

    .card-title-text {
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0 0 8px 0;
        line-height: 1.25;
    }
    .card-desc-text {
        font-size: 13.5px;
        color: #475569;
        line-height: 1.55;
        margin-bottom: 18px;
    }
    .card-action-cue {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12.5px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 8px;
        width: fit-content;
        transition: all 0.15s ease;
    }
    .cue-blue {
        color: #1D4ED8;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
    }
    .feature-card:hover .cue-blue {
        background: #DBEAFE;
    }
    .cue-teal {
        color: #0F766E;
        background: #F0FDFA;
        border: 1px solid #99F6E4;
    }
    .feature-card:hover .cue-teal {
        background: #CCFBF1;
    }
    .cue-emerald {
        color: #15803D;
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
    }
    .feature-card:hover .cue-emerald {
        background: #DCFCE7;
    }
    .cue-purple {
        color: #7E22CE;
        background: #FAF5FF;
        border: 1px solid #E9D5FF;
    }
    .feature-card:hover .cue-purple {
        background: #F3E8FF;
    }
    .cue-indigo {
        color: #6D28D9;
        background: #F5F3FF;
        border: 1px solid #DDD6FE;
    }
    .feature-card:hover .cue-indigo {
        background: #EDE9FE;
    }
    .cue-orange {
        color: #C2410C;
        background: #FFF7ED;
        border: 1px solid #FED7AA;
    }
    .feature-card:hover .cue-orange {
        background: #FFEDD5;
    }
    .cue-coral {
        color: #BE123C;
        background: #FFF1F2;
        border: 1px solid #FECDD3;
    }
    .feature-card:hover .cue-coral {
        background: #FFE4E6;
    }

    /* Dimmed, Soft Action Buttons */
    div.st-key-btn_card_overview button {
        background-color: #FFFFFF !important;
        color: #1D4ED8 !important;
        border: 1.5px solid #BFDBFE !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_overview button:hover {
        background-color: #EFF6FF !important;
        border-color: #3B82F6 !important;
        color: #1E40AF !important;
    }
    div.st-key-btn_card_indicators button {
        background-color: #FFFFFF !important;
        color: #0F766E !important;
        border: 1.5px solid #99F6E4 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(13, 148, 136, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_indicators button:hover {
        background-color: #F0FDFA !important;
        border-color: #14B8A6 !important;
        color: #115E59 !important;
    }
    div.st-key-btn_card_state button {
        background-color: #FFFFFF !important;
        color: #15803D !important;
        border: 1.5px solid #BBF7D0 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(22, 163, 74, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_state button:hover {
        background-color: #F0FDF4 !important;
        border-color: #16A34A !important;
        color: #166534 !important;
    }
    div.st-key-btn_card_phillips button {
        background-color: #FFFFFF !important;
        color: #7E22CE !important;
        border: 1.5px solid #E9D5FF !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(147, 51, 234, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_phillips button:hover {
        background-color: #FAF5FF !important;
        border-color: #9333EA !important;
        color: #6B21A8 !important;
    }
    div.st-key-btn_card_forecast button {
        background-color: #FFFFFF !important;
        color: #C2410C !important;
        border: 1.5px solid #FED7AA !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(234, 88, 12, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_forecast button:hover {
        background-color: #FFF7ED !important;
        border-color: #F97316 !important;
        color: #9A3412 !important;
    }
    div.st-key-btn_card_india button {
        background-color: #FFFFFF !important;
        color: #6D28D9 !important;
        border: 1.5px solid #DDD6FE !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(124, 58, 237, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_india button:hover {
        background-color: #F5F3FF !important;
        border-color: #7C3AED !important;
        color: #5B21B6 !important;
    }
    div.st-key-btn_card_policy button {
        background-color: #FFFFFF !important;
        color: #BE123C !important;
        border: 1.5px solid #FECDD3 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-bottom: 18px !important;
        box-shadow: 0 1px 3px rgba(220, 38, 38, 0.08) !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_card_policy button:hover {
        background-color: #FFF1F2 !important;
        border-color: #F43F5E !important;
        color: #9F1239 !important;
    }

    /* Elevated KPI Cards with Micro-Elevation */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        border-color: #CBD5E1;
    }
    .kpi-tag-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-tag {
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: #64748B;
        text-transform: uppercase;
    }
    .kpi-freq-badge {
        font-size: 10px;
        font-weight: 600;
        color: #0F172A;
        background: #F1F5F9;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .kpi-number {
        font-size: 25px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.15;
        margin-bottom: 8px;
    }
    .kpi-pill-pos {
        background: #DCFCE7;
        color: #15803D;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        width: fit-content;
    }
    .kpi-pill-neg {
        background: #FEE2E2;
        color: #B91C1C;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        width: fit-content;
    }
    .kpi-pill-neutral {
        background: #F1F5F9;
        color: #475569;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        width: fit-content;
    }
    .kpi-footer-sub {
        font-size: 11px;
        color: #64748B;
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #F1F5F9;
        line-height: 1.35;
    }

    /* Content Cards & Sections */
    .content-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .content-card-header {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: #FF5200;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .content-card-title {
        font-size: 19px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }
    .content-card-sub {
        font-size: 13px;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 16px;
    }

    /* Segmented Control Styling */
    [data-testid="stSegmentedControl"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 4px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
        margin-bottom: 18px !important;
    }
    [data-testid="stSegmentedControl"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.15) !important;
    }

    /* Streamlit Tabs Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 13px;
        color: #64748B;
    }
    .stTabs [aria-selected="true"] {
        color: #FF5200 !important;
        border-bottom: 2px solid #FF5200 !important;
    }

    /* Clean Sidebar Light Theme */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #334155 !important;
    }

    /* Data Provenance Card Beside Graphs */
    .provenance-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 14px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 10px;
    }
    .provenance-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2px;
    }
    .provenance-tag {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: #FF5200;
        text-transform: uppercase;
    }
    .provenance-badge-live {
        font-size: 9.5px;
        font-weight: 700;
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
        padding: 2px 7px;
        border-radius: 9999px;
    }
    .provenance-badge-demo {
        font-size: 9.5px;
        font-weight: 700;
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 2px 7px;
        border-radius: 9999px;
    }
    .provenance-badge-sim {
        font-size: 9.5px;
        font-weight: 700;
        background: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
        padding: 2px 7px;
        border-radius: 9999px;
    }
    .provenance-title {
        font-size: 13.5px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.25;
        margin-top: 2px;
    }
    .provenance-field {
        border-top: 1px solid #F1F5F9;
        padding-top: 7px;
    }
    .provenance-label {
        font-size: 9.5px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 1px;
    }
    .provenance-val {
        font-size: 11.5px;
        font-weight: 600;
        color: #0F172A;
        line-height: 1.35;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Standard benchmark conversion rate: USD to Indian Rupees (INR)
USD_TO_INR = 83.0


@st.cache_data(ttl=3600, show_spinner=False)
def load_macro_data(api_key: str, force_demo: bool):
    """Cached loader for FRED macroeconomic series with INR conversion for currency levels.

    Returns:
        tuple: (raw_series_dict, df_harmonized, is_live_data, messages_list, metadata_dict)
    """
    client = FredClient(api_key=api_key)
    raw_series, is_live, messages, metadata = client.fetch_all_core_series(
        start_date="1990-01-01", force_demo=force_demo
    )
    if not raw_series:
        return {}, pd.DataFrame(), is_live, messages, {}

    harmonized = harmonize_macro_series(raw_series)
    augmented = calculate_derived_indicators(harmonized)
    # Convert Real GDP from USD to Indian Rupees (₹ Billions)
    if "GDPC1" in augmented.columns:
        augmented["GDPC1"] = augmented["GDPC1"] * USD_TO_INR
    return raw_series, augmented, is_live, messages, metadata


@st.cache_data(ttl=3600, show_spinner=False)
def load_world_bank_data(country_code: str, start_yr: int, end_yr: int):
    """Cached loader for World Bank country indicators."""
    wb_client = WorldBankClient()
    return wb_client.fetch_country_overview(country_code, start_year=start_yr, end_year=end_yr)


@st.cache_data(ttl=3600, show_spinner=False)
def load_india_forecasting_data():
    """Cached loader for genuine Indian macroeconomic time series and target forecasting datasets."""
    client = IndiaDataClient()
    return build_india_forecasting_datasets(client)


@st.cache_data(ttl=3600, show_spinner=False)
def load_state_intelligence_data():
    """Cached loader for authentic Indian state-level economic statistics (RBI DBIE & MoSPI PLFS)."""
    client = IndiaStateDataClient()
    return client.build_state_master_dataset()


# ==============================================================================
# SIDEBAR SETTINGS & AUXILIARY CONTROLS
# ==============================================================================
has_env_key = bool(FRED_API_KEY and FRED_API_KEY != "your_fred_api_key_here" and len(FRED_API_KEY) >= 16)
if "data_mode" not in st.session_state:
    st.session_state["data_mode"] = "Live FRED API" if has_env_key else "Demonstration Dataset"

st.sidebar.markdown(
    """
    <div style="padding: 6px 0 12px 0;">
        <div style="font-size: 16px; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">EcoSim Terminal Settings</div>
        <div style="font-size: 11.5px; color: #64748B;">Data feed configuration & filters</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Data Feed Mode Selection
mode_options = ["Live FRED API", "Demonstration Dataset"]
selected_mode = st.sidebar.radio(
    "DATA FEED MODE",
    mode_options,
    index=0 if st.session_state["data_mode"] == "Live FRED API" else 1,
    help="Select 'Live FRED API' to query the St. Louis Fed with your API key, or 'Demonstration Dataset' for offline historical US benchmarks.",
)
st.session_state["data_mode"] = selected_mode
force_demo_mode = (selected_mode == "Demonstration Dataset")

# Observation Date Filter
st.sidebar.markdown("<div style='font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-top: 12px;'>Observation Date Range</div>", unsafe_allow_html=True)
date_range = st.sidebar.slider(
    "Observation Range:",
    min_value=1990,
    max_value=2024,
    value=(1995, 2024),
    step=1,
    label_visibility="collapsed",
)

# Demonstration Walkthrough Guide Expander
with st.sidebar.expander("🎓 5-Minute Demo Sequence", expanded=False):
    st.markdown(
        """
        <div style="font-size: 11.5px; color: #334155; line-height: 1.55;">
            <b>1. Homepage:</b> Interactive 4-card hub showcasing core economic modules.<br><br>
            <b>2. Overview:</b> Introduce core macro indicators, release cadences, Misery Index, and real interest rate.<br><br>
            <b>3. Indicators:</b> Tour historical timelines, recession shocks (2008, 2020), and quarterly/monthly differences.<br><br>
            <b>4. Inflation Forecast:</b> Present Ridge Regression predicting next-quarter inflation with zero lookahead leakage.<br><br>
            <b>5. Policy Lab:</b> Test fiscal spending multiplier (ΔG in ₹B) and monetary interest-rate shock (Δr) comparative statics.<br><br>
            <b>6. Data Sources:</b> Review FRED series, keyless World Bank annual data, and methodology boundaries.
        </div>
        """,
        unsafe_allow_html=True,
    )

# API Configuration Expander
with st.sidebar.expander("API Configuration & Setup", expanded=False):
    custom_key = st.text_input(
        "FRED Key:",
        value="",
        type="password",
        placeholder="Using key from .env" if has_env_key else "Paste FRED API key here",
        help="Optional: Paste a key directly. It is never logged, exposed in DOM, or committed to version control.",
    )
    active_key = custom_key.strip() if custom_key.strip() else FRED_API_KEY
    if has_env_key:
        st.caption("✅ Local .env configuration detected.")
    else:
        st.caption("ℹ️ Add `FRED_API_KEY=your_key` to local `.env` to enable live mode permanently.")
    st.caption("World Bank API operates keylessly out-of-the-box.")

# Sidebar Refresh Action
if st.sidebar.button("🔄 Refresh Application Data", width="stretch"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size: 10.5px; color: #94A3B8; line-height: 1.4;">
        EcoSim — Macroeconomic Platform<br>
        ML: Ridge Regression (L₂ Regularization)<br>
        Simulations: Keynesian k • Simplified IS–LM
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# DATA INGESTION
# ==============================================================================
with st.spinner("Connecting to macroeconomic data pipeline..."):
    raw_series, df_macro, is_live_data, load_messages, meta_series = load_macro_data(
        active_key, force_demo=force_demo_mode
    )

# Handle Missing Key or Failed Live Data
if df_macro.empty:
    st.markdown("<h2 style='margin:0; font-weight:800; color:#0F172A;'>Macroeconomic Data Unavailable</h2>", unsafe_allow_html=True)
    if not force_demo_mode:
        st.warning(
            "⚠️ **Live FRED API Ingestion Unsuccessful**\n\n"
            + ("\n".join([f"- {m}" for m in load_messages]) if load_messages else "No active FRED API key detected in `.env`.")
        )
        st.markdown(
            """
            ### How to Configure Live FRED Data
            1. Sign up for a free FRED API key at [St. Louis Fed FRED](https://fred.stlouisfed.org/docs/api/api_key.html).
            2. Add your key to the project root `.env` file:
               ```bash
               FRED_API_KEY=your_actual_32_character_key_here
               ```
            3. Or paste your key directly into the sidebar under **API Configuration & Setup**.
            4. Click **Refresh Application Data** in the sidebar.

            ### Or Continue Instantly in Demonstration Mode
            Click below to explore all features immediately with realistic historical US macroeconomic benchmark data (1990–2024).
            """
        )
        if st.button("👉 Switch to Demonstration Dataset (1990–2024)", width="stretch"):
            st.session_state["data_mode"] = "Demonstration Dataset"
            st.rerun()
    else:
        st.error("Demonstration dataset could not be generated. Please restart the application.")
    st.stop()

# Filter by selected date range
df_filtered = df_macro[
    (df_macro["date"].dt.year >= date_range[0]) & (df_macro["date"].dt.year <= date_range[1])
].copy().reset_index(drop=True)


# ==============================================================================
# NAVIGATION STATE SYNCHRONIZATION
# ==============================================================================
nav_options = [
    "Overview",
    "Economic Indicators",
    "State Intelligence",
    "Phillips Curve",
    "Inflation Forecast",
    "India Macro Forecast",
    "Policy Lab",
    "Data Sources",
]

# Ensure the homepage is the initial view when the application opens
if "top_nav_bar" not in st.session_state:
    st.session_state["top_nav_bar"] = None

# Query Parameter Support (e.g. ?page=Overview or ?page=Home)
if "page" in st.query_params:
    req_page = st.query_params.get("page")
    if req_page in nav_options:
        st.session_state["top_nav_bar"] = req_page
    elif req_page in ("Home", "home", "hub"):
        st.session_state["top_nav_bar"] = None
    del st.query_params["page"]


def navigate_to(page_target: str | None):
    """Callback to update active navigation page."""
    st.session_state["top_nav_bar"] = page_target


# ==============================================================================
# TOP BRAND NAVBAR
# ==============================================================================
col_nav_brand, col_nav_status = st.columns([0.62, 0.38])

with col_nav_brand:
    st.markdown(
        """
        <a href="?page=Home" target="_self" class="brand-container">
            <div class="brand-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 19.5V4.5C4 4.22386 4.22386 4 4.5 4H19.5" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                    <path d="M8 15L12 10L15 13L20 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="brand-title">EcoSim</span>
                    <span class="brand-pill">The Economy, Explained</span>
                </div>
                <div style="font-size: 12px; color: #64748B; margin-top: 3px;">
                    Real-time macroeconomic intelligence, regularized forecasting & policy simulations
                </div>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

with col_nav_status:
    if force_demo_mode:
        status_badge = '<span class="badge-demo-pill"><span class="pulse-dot-demo"></span> DEMO DATASET (1990–2024)</span>'
    elif is_live_data:
        status_badge = '<span class="badge-live-pill"><span class="pulse-dot-live"></span> LIVE FRED & WORLD BANK API</span>'
    else:
        status_badge = '<span class="badge-demo-pill"><span class="pulse-dot-demo"></span> DEMO SNAPSHOT (FRED KEY OPTIONAL)</span>'

    gdp_dt_meta = meta_series.get("GDPC1", {}).get("latest_date")
    cpi_dt_meta = meta_series.get("CPIAUCSL", {}).get("latest_date")
    gdp_lbl = f"Q{gdp_dt_meta.quarter} {gdp_dt_meta.year}" if gdp_dt_meta is not None else "Q1 2024"
    cpi_lbl = cpi_dt_meta.strftime("%b %Y") if cpi_dt_meta is not None else "Latest"

    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 4px;">
            {status_badge}
            <div style="font-size: 11px; color: #64748B; margin-top: 5px;">
                Latest Observed: Real GDP <b>{gdp_lbl}</b> • CPI <b>{cpi_lbl}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# TOP APPLICATION NAVIGATION BAR (Preserving Exact Six Options & Styling)
# ==============================================================================
selected_page = st.segmented_control(
    "Navigation Menu",
    options=nav_options,
    label_visibility="collapsed",
    key="top_nav_bar",
)


# Helper for rendering elevated KPI cards on the Overview page
def render_kpi(
    col,
    title: str,
    value_str: str,
    sub_str: str,
    delta_val: float | None = None,
    delta_suffix: str = "%",
    invert_color: bool = False,
    delta_label: str = "Period Change",
    freq_badge: str = "Monthly",
):
    pill_html = ""
    if delta_val is not None and not np.isnan(delta_val):
        is_pos = delta_val > 0
        is_zero = abs(delta_val) < 1e-4
        if is_zero:
            pill_cls = "kpi-pill-neutral"
            sign = "±"
        else:
            if invert_color:
                pill_cls = "kpi-pill-neg" if is_pos else "kpi-pill-pos"
            else:
                pill_cls = "kpi-pill-pos" if is_pos else "kpi-pill-neg"
            sign = "+" if is_pos else ""
        pill_html = f"<div class='{pill_cls}'>{sign}{delta_val:.2f}{delta_suffix} {delta_label}</div>"
    else:
        pill_html = "<div class='kpi-pill-neutral'>Baseline</div>"

    col.markdown(
        f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-tag-row">
                    <span class="kpi-tag">{title}</span>
                    <span class="kpi-freq-badge">{freq_badge}</span>
                </div>
                <div class="kpi-number">{value_str}</div>
                {pill_html}
            </div>
            <div class="kpi-footer-sub">{sub_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Helper for rendering institutional data provenance cards beside graphs
def render_data_provenance_card(
    col,
    title: str,
    source_api: str,
    api_key_status: str,
    series_code: str,
    frequency: str,
    currency_unit: str,
    badge_type: str = "live",
    badge_text: str = "LIVE FEED",
    notes: str = "",
):
    """Renders a data provenance metadata card beside charts."""
    badge_class = {
        "live": "provenance-badge-live",
        "demo": "provenance-badge-demo",
        "sim": "provenance-badge-sim",
        "wb": "provenance-badge-live",
    }.get(badge_type, "provenance-badge-live")

    note_html = (
        f"""
        <div class="provenance-field">
            <div class="provenance-label">Methodology & Alignment</div>
            <div class="provenance-val" style="font-size: 11px; color: #475569; font-weight: 500;">{notes}</div>
        </div>
        """
        if notes
        else ""
    )

    col.markdown(
        f"""
        <div class="provenance-card">
            <div>
                <div class="provenance-header">
                    <span class="provenance-tag">DATA PROVENANCE</span>
                    <span class="{badge_class}">{badge_text}</span>
                </div>
                <div class="provenance-title">{title}</div>
            </div>
            <div class="provenance-field">
                <div class="provenance-label">Origin & Provider</div>
                <div class="provenance-val">{source_api}</div>
            </div>
            <div class="provenance-field">
                <div class="provenance-label">API Key & Credential</div>
                <div class="provenance-val">{api_key_status}</div>
            </div>
            <div class="provenance-field">
                <div class="provenance-label">Series / Model Code</div>
                <div class="provenance-val"><code>{series_code}</code></div>
            </div>
            <div class="provenance-field">
                <div class="provenance-label">Reporting Unit & Currency</div>
                <div class="provenance-val">{currency_unit}</div>
            </div>
            <div class="provenance-field">
                <div class="provenance-label">Observation Frequency</div>
                <div class="provenance-val">{frequency}</div>
            </div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# STARTING HOMEPAGE: FOUR LARGE COLOURFUL FEATURE CARDS (2x2 GRID)
# ==============================================================================
if selected_page is None:
    # Polished Welcome Heading & Concise Subtitle
    st.markdown(
        """
        <div class="home-welcome-header">
            <div class="home-welcome-eyebrow">Macroeconomic Intelligence Platform</div>
            <h1 class="home-welcome-title">Explore the Economy with EcoSim</h1>
            <p class="home-welcome-subtitle">
                Economic indicators, inflation forecasting, and policy simulation in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ROW 1: TWO CARDS (Overview & Economic Indicators)
    r1_c1, r1_c2 = st.columns(2)

    # 1. ECONOMIC OVERVIEW (Soft Dimmed Blue)
    with r1_c1:
        st.markdown(
            """
            <a href="?page=Overview" target="_self" class="feature-card-link">
                <div class="feature-card card-blue">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-blue">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M18 20V10"/>
                                    <path d="M12 20V4"/>
                                    <path d="M6 20v-6"/>
                                    <path d="M3 20h18"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-blue">Core Analytics</span>
                        </div>
                        <div class="card-title-text">ECONOMIC OVERVIEW</div>
                        <div class="card-desc-text">
                            Explore the latest GDP, inflation, unemployment, and interest-rate indicators in Indian Rupees (₹) and standard metrics.
                        </div>
                    </div>
                    <div class="card-action-cue cue-blue">
                        <span>Launch Overview</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Launch Economic Overview →",
            key="btn_card_overview",
            on_click=navigate_to,
            args=("Overview",),
            width="stretch",
        )

    # 2. ECONOMIC INDICATORS (Soft Dimmed Teal)
    with r1_c2:
        st.markdown(
            """
            <a href="?page=Economic%20Indicators" target="_self" class="feature-card-link">
                <div class="feature-card card-teal">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-teal">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0D9488" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                                    <polyline points="16 7 22 7 22 13"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-teal">Time Series</span>
                        </div>
                        <div class="card-title-text">ECONOMIC INDICATORS</div>
                        <div class="card-desc-text">
                            Explore historical economic trends, synchronized timelines, and compare macroeconomic indicators.
                        </div>
                    </div>
                    <div class="card-action-cue cue-teal">
                        <span>Compare Indicators</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Explore Economic Indicators →",
            key="btn_card_indicators",
            on_click=navigate_to,
            args=("Economic Indicators",),
            width="stretch",
        )

    # ROW 2: TWO CARDS (State Economic Intelligence & Phillips Curve)
    r2_c1, r2_c2 = st.columns(2)

    # 3. STATE ECONOMIC INTELLIGENCE (Soft Dimmed Emerald)
    with r2_c1:
        st.markdown(
            """
            <a href="?page=State%20Intelligence" target="_self" class="feature-card-link">
                <div class="feature-card card-emerald">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-emerald">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#15803D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 21h18"/>
                                    <path d="M5 21V7l8-4v18"/>
                                    <path d="M19 21V11l-6-4"/>
                                    <path d="M9 9h1"/>
                                    <path d="M9 13h1"/>
                                    <path d="M9 17h1"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-emerald">Regional Accounts</span>
                        </div>
                        <div class="card-title-text">STATE ECONOMIC INTELLIGENCE</div>
                        <div class="card-desc-text">
                            Explore state-level GSDP, per-capita income, PLFS labour statistics, and the transparent Economic Stress Index.
                        </div>
                    </div>
                    <div class="card-action-cue cue-emerald">
                        <span>Explore States</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Explore State Intelligence →",
            key="btn_card_state",
            on_click=navigate_to,
            args=("State Intelligence",),
            width="stretch",
        )

    # 4. PHILLIPS CURVE (Soft Dimmed Purple)
    with r2_c2:
        st.markdown(
            """
            <a href="?page=Phillips%20Curve" target="_self" class="feature-card-link">
                <div class="feature-card card-purple">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-purple">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7E22CE" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="9"/>
                                    <path d="M8 12s1.5-2 4-2 4 2 4 2"/>
                                    <line x1="9" y1="9" x2="9.01" y2="9"/>
                                    <line x1="15" y1="9" x2="15.01" y2="9"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-purple">Macroeconomic Theory</span>
                        </div>
                        <div class="card-title-text">PHILLIPS CURVE</div>
                        <div class="card-desc-text">
                            Investigate the empirical trade-off between inflation and unemployment across historical economic cycles.
                        </div>
                    </div>
                    <div class="card-action-cue cue-purple">
                        <span>Analyze Trade-Off</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Explore Phillips Curve →",
            key="btn_card_phillips",
            on_click=navigate_to,
            args=("Phillips Curve",),
            width="stretch",
        )

    # ROW 3: TWO CARDS (Inflation Forecast & India Macro Forecast)
    r3_c1, r3_c2 = st.columns(2)

    # 5. INFLATION FORECAST (Soft Dimmed Orange)
    with r3_c1:
        st.markdown(
            """
            <a href="?page=Inflation%20Forecast" target="_self" class="feature-card-link">
                <div class="feature-card card-orange">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-orange">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                                    <circle cx="12" cy="12" r="3" fill="#EA580C"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-orange">Machine Learning</span>
                        </div>
                        <div class="card-title-text">INFLATION FORECAST</div>
                        <div class="card-desc-text">
                            Explore next-quarter inflation predictions generated by Ridge Regression without lookahead leakage.
                        </div>
                    </div>
                    <div class="card-action-cue cue-orange">
                        <span>Generate Forecast</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "View Inflation Forecast →",
            key="btn_card_forecast",
            on_click=navigate_to,
            args=("Inflation Forecast",),
            width="stretch",
        )

    # 6. INDIA MACRO FORECAST (Soft Dimmed Indigo)
    with r3_c2:
        st.markdown(
            """
            <a href="?page=India%20Macro%20Forecast" target="_self" class="feature-card-link">
                <div class="feature-card card-indigo">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-indigo">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"/>
                                    <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
                                    <path d="M2 12h20"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-indigo">Indian Economy ML</span>
                        </div>
                        <div class="card-title-text">INDIA MACRO FORECAST</div>
                        <div class="card-desc-text">
                            Multi-indicator regularized Ridge forecasting for Indian CPI inflation, Real GDP growth, and industrial production (IIP).
                        </div>
                    </div>
                    <div class="card-action-cue cue-indigo">
                        <span>Explore India Models</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Explore India Macro Forecast →",
            key="btn_card_india",
            on_click=navigate_to,
            args=("India Macro Forecast",),
            width="stretch",
        )

    # ROW 4: POLICY LAB & DATA SOURCES
    r4_c1, r4_c2 = st.columns(2)

    # 7. POLICY LAB (Soft Dimmed Coral)
    with r4_c1:
        st.markdown(
            """
            <a href="?page=Policy%20Lab" target="_self" class="feature-card-link">
                <div class="feature-card card-coral">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble bubble-coral">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="4" y1="21" x2="4" y2="14"/>
                                    <line x1="4" y1="10" x2="4" y2="3"/>
                                    <line x1="12" y1="21" x2="12" y2="12"/>
                                    <line x1="12" y1="8" x2="12" y2="3"/>
                                    <line x1="20" y1="21" x2="20" y2="16"/>
                                    <line x1="20" y1="12" x2="20" y2="3"/>
                                    <line x1="1" y1="14" x2="7" y2="14"/>
                                    <line x1="9" y1="8" x2="15" y2="8"/>
                                    <line x1="17" y1="16" x2="23" y2="16"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag tag-coral">Policy Simulation</span>
                        </div>
                        <div class="card-title-text">POLICY LAB</div>
                        <div class="card-desc-text">
                            Experiment with government-spending (in ₹B) and interest-rate shocks across two macroeconomic models.
                        </div>
                    </div>
                    <div class="card-action-cue cue-coral">
                        <span>Simulate Policies</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Enter Policy Simulation Lab →",
            key="btn_card_policy",
            on_click=navigate_to,
            args=("Policy Lab",),
            width="stretch",
        )

    # 6. DATA SOURCES & TRANSPARENCY CARD (Neutral Slate)
    with r3_c2:
        st.markdown(
            """
            <a href="?page=Data%20Sources" target="_self" class="feature-card-link">
                <div class="feature-card" style="background:linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 60%, #F1F5F9 100%); border:1.5px solid #CBD5E1;">
                    <div>
                        <div class="card-top-row">
                            <div class="card-icon-bubble" style="background:#F1F5F9; border:1px solid #CBD5E1;">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <ellipse cx="12" cy="5" rx="9" ry="3"/>
                                    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                                    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                                </svg>
                            </div>
                            <span class="card-pill-tag" style="background:#F1F5F9; color:#475569; border:1px solid #CBD5E1;">DATA PROVENANCE</span>
                        </div>
                        <div class="card-title-text">DATA SOURCES & METHODOLOGY</div>
                        <div class="card-desc-text">
                            Inspect official RBI DBIE, MoSPI eSankhyiki, FRED, and World Bank API inventories, indicator codes, and disclaimers.
                        </div>
                    </div>
                    <div class="card-action-cue" style="color:#334155; background:#F1F5F9; border:1px solid #CBD5E1;">
                        <span>View Data Sources</span>
                        <span>→</span>
                    </div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Explore Data Sources & Methodology →",
            key="btn_card_sources",
            on_click=navigate_to,
            args=("Data Sources",),
            width="stretch",
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Platform Data Transparency & Sources Callout Banner
    st.markdown(
        """
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:18px 24px; box-shadow:0 1px 3px rgba(15,23,42,0.04); display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:11px; font-weight:700; color:#FF5200; text-transform:uppercase; letter-spacing:0.06em;">DATA INTEGRITY & METHODOLOGY</div>
                <div style="font-size:14px; font-weight:700; color:#0F172A; margin:2px 0;">Looking for series documentation, World Bank data, or model boundaries?</div>
                <div style="font-size:12.5px; color:#64748B;">Access authentic Federal Reserve (FRED) time-series inventories, cross-country datasets, and econometric proofs.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_src_btn, _ = st.columns([0.35, 0.65])
    with col_src_btn:
        st.button(
            "Explore Data Sources & Methodology →",
            key="btn_home_datasources",
            on_click=navigate_to,
            args=("Data Sources",),
            width="stretch",
        )


# ==============================================================================
# 1. OVERVIEW DASHBOARD
# ==============================================================================
elif selected_page == "Overview":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_overview", on_click=navigate_to, args=(None,))

    # Hero Showcase Banner
    st.markdown(
        """
        <div style="background:linear-gradient(135deg, #FFFFFF 0%, #FFFBF7 50%, #F8FAFC 100%); border:1px solid #FED7AA; border-radius:16px; padding:22px 26px; margin-bottom:20px; box-shadow:0 4px 18px rgba(255,82,0,0.04);">
            <div style="font-size:24px; font-weight:800; color:#0F172A; letter-spacing:-0.03em; margin-bottom:4px;">Economic Overview & Core Indicators</div>
            <div style="font-size:13.5px; color:#475569; max-width:860px; line-height:1.55; margin-bottom:14px;">
                Real-time macroeconomic tracking powered by Federal Reserve (FRED) time-series, derived monetary stability indicators, and release cadences.
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
                <span class="hero-chip">🏛️ 5 Core FRED Macro Time Series</span>
                <span class="hero-chip">🔮 Ridge Regularized L₂ Forecaster</span>
                <span class="hero-chip">🧪 2 Classical Macro Policy Simulators</span>
                <span class="hero-chip">🌐 Keyless World Bank API V2 Data</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 5 KPI Cards Row with honest observation cadences
    if not df_filtered.empty:
        latest = df_filtered.iloc[-1]
        prev = df_filtered.iloc[-2] if len(df_filtered) > 1 else latest

        c1, c2, c3, c4, c5 = st.columns(5)

        # 1. Real GDP (Quarterly series)
        gdp_val = latest.get("GDPC1", 0)
        gdp_prev_val = df_filtered["GDPC1"].dropna().iloc[-2] if len(df_filtered["GDPC1"].dropna()) > 1 else gdp_val
        gdp_delta = ((gdp_val - gdp_prev_val) / gdp_prev_val * 100) if gdp_prev_val > 0 else 0
        gdp_meta_date = meta_series.get("GDPC1", {}).get("latest_date")
        gdp_date_str = f"Q{gdp_meta_date.quarter} {gdp_meta_date.year}" if gdp_meta_date is not None else "Quarterly"
        render_kpi(
            c1,
            "REAL GDP",
            f"₹{gdp_val:,.0f}B",
            f"Chained Rupees (₹83/USD) · {gdp_date_str}",
            delta_val=gdp_delta,
            delta_suffix="%",
            delta_label="QoQ Change",
            freq_badge="Quarterly",
        )

        # 2. YoY Inflation (Monthly series)
        inf_val = latest.get("inflation_yoy", 0)
        inf_delta = inf_val - prev.get("inflation_yoy", inf_val)
        cpi_meta_date = meta_series.get("CPIAUCSL", {}).get("latest_date")
        cpi_date_str = cpi_meta_date.strftime("%b %Y") if cpi_meta_date is not None else latest["date"].strftime("%b %Y")
        render_kpi(
            c2,
            "YOY INFLATION",
            f"{inf_val:.2f}%",
            f"Headline CPI-U basket · {cpi_date_str}",
            delta_val=inf_delta,
            delta_suffix=" pts",
            invert_color=True,
            delta_label="MoM Shift",
            freq_badge="Monthly",
        )

        # 3. Unemployment Rate (Monthly series)
        unemp_val = latest.get("UNRATE", 0)
        unemp_delta = unemp_val - prev.get("UNRATE", unemp_val)
        un_meta_date = meta_series.get("UNRATE", {}).get("latest_date")
        un_date_str = un_meta_date.strftime("%b %Y") if un_meta_date is not None else latest["date"].strftime("%b %Y")
        render_kpi(
            c3,
            "UNEMPLOYMENT",
            f"{unemp_val:.1f}%",
            f"Civilian labor force · {un_date_str}",
            delta_val=unemp_delta,
            delta_suffix=" pts",
            invert_color=True,
            delta_label="MoM Shift",
            freq_badge="Monthly",
        )

        # 4. Federal Funds Rate (Monthly series)
        fed_val = latest.get("FEDFUNDS", 0)
        fed_delta = fed_val - prev.get("FEDFUNDS", fed_val)
        fed_meta_date = meta_series.get("FEDFUNDS", {}).get("latest_date")
        fed_date_str = fed_meta_date.strftime("%b %Y") if fed_meta_date is not None else latest["date"].strftime("%b %Y")
        render_kpi(
            c4,
            "FED FUNDS RATE",
            f"{fed_val:.2f}%",
            f"Effective overnight rate · {fed_date_str}",
            delta_val=fed_delta,
            delta_suffix=" pts",
            delta_label="MoM Shift",
            freq_badge="Monthly",
        )

        # 5. 10-Year Treasury Yield (Monthly series)
        gs10_val = latest.get("GS10", 0)
        gs10_delta = gs10_val - prev.get("GS10", gs10_val)
        gs_meta_date = meta_series.get("GS10", {}).get("latest_date")
        gs_date_str = gs_meta_date.strftime("%b %Y") if gs_meta_date is not None else latest["date"].strftime("%b %Y")
        render_kpi(
            c5,
            "10Y TREASURY",
            f"{gs10_val:.2f}%",
            f"Constant maturity yield · {gs_date_str}",
            delta_val=gs10_delta,
            delta_suffix=" pts",
            delta_label="MoM Shift",
            freq_badge="Monthly",
        )

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Primary Multi-Series Interactive Chart Section
        st.markdown(
            """
            <div class="content-card">
                <div class="content-card-header">INTERACTIVE TIMELINE</div>
                <div class="content-card-title">Unified Macroeconomic Chronology</div>
                <div class="content-card-sub">Select indicators below to compare synchronized trends, policy pivots, and historical cycles.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sel_cols = st.multiselect(
            "Select series to plot:",
            options=["inflation_yoy", "UNRATE", "FEDFUNDS", "GS10", "real_interest_rate", "misery_index"],
            default=["inflation_yoy", "UNRATE", "FEDFUNDS", "GS10"],
            format_func=lambda x: {
                "inflation_yoy": "YoY Inflation Rate (% YoY, Monthly)",
                "UNRATE": "Civilian Unemployment Rate (%, Monthly)",
                "FEDFUNDS": "Effective Fed Funds Rate (%, Monthly)",
                "GS10": "10-Year Treasury Yield (%, Monthly)",
                "real_interest_rate": "Approx. Real Rate (% Annualized, Fed Funds − Inflation)",
                "misery_index": "Misery Index (% Points, Inflation + Unemployment)",
            }.get(x, x),
            label_visibility="collapsed",
        )

        if sel_cols:
            col_c, col_p = st.columns([0.76, 0.24])
            with col_c:
                fig_multi = plot_multi_series_selector(df_filtered, sel_cols)
                st.plotly_chart(fig_multi, width="stretch")
            with col_p:
                api_status_str = "Authenticated via FRED_API_KEY in .env" if is_live_data else "Demonstration Snapshot (1990–2024)"
                b_type = "live" if is_live_data else "demo"
                b_txt = "LIVE FRED" if is_live_data else "DEMO SNAPSHOT"
                series_code_str = ", ".join(sel_cols)
                render_data_provenance_card(
                    col=col_p,
                    title="FRED Multi-Series Feed",
                    source_api="Federal Reserve Bank of St. Louis (FRED)",
                    api_key_status=api_status_str,
                    series_code=series_code_str,
                    frequency="Monthly / Quarterly Harmonized",
                    currency_unit="Indian Rupees (₹) [Converted @ ₹83.00/USD] & Rates (%)",
                    badge_type=b_type,
                    badge_text=b_txt,
                    notes="Harmonized to monthly start dates. Real GDP forward-filled within 3-month release window."
                )
        else:
            st.info("Select at least one economic series above to display the time-series chart.")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Derived Indicators Panels (Misery Index & Approximate Real Interest Rate)
        col_misery, col_real = st.columns(2)
        with col_misery:
            misery_val = latest.get("misery_index", 0)
            misery_rating = "Low (<6%)" if misery_val < 6.0 else ("Moderate (6–9%)" if misery_val <= 9.0 else "Elevated (>9%)")
            st.markdown(
                f"""
                <div class="content-card">
                    <div class="content-card-header">DERIVED INDICATOR: OKUN'S MISERY INDEX</div>
                    <div style="font-size: 27px; font-weight: 800; color: #0F172A; margin: 4px 0;">{misery_val:.2f}%</div>
                    <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                        <b>Formula:</b> Inflation Rate ({inf_val:.2f}%) + Unemployment Rate ({unemp_val:.1f}%)<br>
                        <b>Macro Assessment:</b> <span style="font-weight:700; color:#FF5200;">{misery_rating}</span>.<br>
                        <b>Economic Significance:</b> Formulated by Arthur Okun in the 1970s as a composite measure of civilian economic discomfort. Higher readings highlight concurrent purchasing power loss and employment fragility.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_real:
            real_val = latest.get("real_interest_rate", 0)
            stance = "Restrictive (Policy Rate > Inflation Rate)" if real_val > 0 else "Accommodative (Policy Rate < Inflation Rate)"
            st.markdown(
                f"""
                <div class="content-card">
                    <div class="content-card-header">DERIVED INDICATOR: APPROXIMATE REAL INTEREST RATE</div>
                    <div style="font-size: 27px; font-weight: 800; color: #0F172A; margin: 4px 0;">{real_val:.2f}%</div>
                    <div style="font-size: 12.5px; color: #475569; line-height: 1.55;">
                        <b>Formula:</b> Fed Funds Rate ({fed_val:.2f}%) − Observed YoY Inflation ({inf_val:.2f}%)<br>
                        <b>Monetary Stance:</b> <span style="font-weight:700; color:#FF5200;">{stance}</span>.<br>
                        <i style="color:#64748B;">Methodological Clarification: Derived directly from backward-looking observed YoY inflation as a transparent proxy for the ex-ante real rate (Fisher relation: r ≈ i − π). It does not substitute for survey-based inflation expectations.</i>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# 2. ECONOMIC INDICATORS
# ==============================================================================
elif selected_page == "Economic Indicators":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_indicators", on_click=navigate_to, args=(None,))

    st.markdown(
        """
        <div class="content-card">
            <div class="content-card-header">EMPIRICAL DATA MATRIX</div>
            <div class="content-card-title">Economic Indicators & Historical Time Series</div>
            <div class="content-card-sub">Inspect, compare, and analyze historical macroeconomic variables across unified chronological timelines.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_overview_charts, tab_regimes, tab_decomposition, tab_global_wb, tab_single_deep, tab_data_table = st.tabs([
        "Synchronized Macro Overview",
        "Economic Regime & Recession Analysis",
        "Inflation Trend Decomposition",
        "Global Macro Comparison (World Bank)",
        "Individual Series Deep Dive",
        "Tabular Data Matrix",
    ])

    with tab_overview_charts:
        col_c, col_p = st.columns([0.76, 0.24])
        with col_c:
            fig_overview = plot_macro_overview(df_filtered)
            st.plotly_chart(fig_overview, use_container_width=True)
        with col_p:
            api_status_str = "Authenticated via FRED_API_KEY in .env" if is_live_data else "Demonstration Snapshot (1990–2024)"
            b_type = "live" if is_live_data else "demo"
            b_txt = "LIVE FRED" if is_live_data else "DEMO SNAPSHOT"
            render_data_provenance_card(
                col=col_p,
                title="FRED Core Macro Matrix",
                source_api="Federal Reserve Bank of St. Louis (FRED)",
                api_key_status=api_status_str,
                series_code="GDPC1, CPIAUCSL, UNRATE, FEDFUNDS",
                frequency="Quarterly (GDP) & Monthly",
                currency_unit="Real GDP in ₹B (@ ₹83/USD), CPI in Index, Rates in %",
                badge_type=b_type,
                badge_text=b_txt,
                notes="Multi-panel chronology covering 1990–2024 with shaded official NBER recession bands."
            )

    with tab_regimes:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:18px 22px; margin-bottom:16px;">
                <div style="font-size:18px; font-weight:800; color:#0F172A; margin-bottom:4px;">Macroeconomic Business-Cycle & Regime Analysis</div>
                <div style="font-size:13px; color:#475569; line-height:1.55;">
                    Evaluates macroeconomic indicator behavior across cyclical expansions and contractions. For the United States, official recession dates are sourced from the <b>NBER Business Cycle Dating Committee</b>. For India, which has no official recession-dating body, analytical slowdown regimes are determined via a <b>transparent statistical rule</b> (≥ 2 consecutive quarters of below-5% Real GDP growth or contraction).
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        regime_framework = st.radio(
            "Select Country & Regime Framework:",
            ["United States (Official NBER Chronology)", "India (Analytical Growth Slowdown Framework)"],
            horizontal=True,
            key="regime_country_radio",
        )

        if "United States" in regime_framework:
            df_us_summary, df_us_episodes = compute_us_regime_statistics(df_filtered)

            col_chart, col_prov = st.columns([0.74, 0.26])
            with col_chart:
                fig_us_regime = plot_regime_comparison_bars(
                    df_us_summary,
                    title="US Macroeconomic Indicators: NBER Expansions vs. Recessions",
                    is_india=False,
                )
                st.plotly_chart(fig_us_regime, use_container_width=True)
            with col_prov:
                render_data_provenance_card(
                    col=col_prov,
                    title="US NBER Business Cycles",
                    source_api="NBER & Federal Reserve Bank of St. Louis (FRED)",
                    api_key_status="Official Business Cycle Chronology",
                    series_code="NBER Recession Dates (1970–2024)",
                    frequency="Monthly / Event Interval",
                    currency_unit="Indicator Averages across Regimes (%)",
                    badge_type="live" if is_live_data else "demo",
                    badge_text="NBER CHRONOLOGY",
                    notes="Recession intervals defined by NBER Business Cycle Dating Committee. Shaded bands represent peaks to troughs."
                )

            st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:16px; margin-bottom:8px;'>1. INDICATOR BEHAVIOR ACROSS EXPANSIONS VS. RECESSIONS</div>", unsafe_allow_html=True)
            st.dataframe(df_us_summary, use_container_width=True, hide_index=True)

            st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:20px; margin-bottom:8px;'>2. OFFICIAL NBER RECESSION EPISODES BREAKDOWN</div>", unsafe_allow_html=True)
            st.dataframe(df_us_episodes, use_container_width=True, hide_index=True)

            with st.expander("Macroeconomic Theory & Pedagogical Interpretation (Expansions vs. Recessions)"):
                st.markdown(
                    """
                    **1. Okun's Law and Labor Market Slack:**
                    During NBER recessions, output decelerates below potential, and firms curtail hiring and initiate layoffs. The civilian unemployment rate surges (e.g., from 4.7% to 10.0% during the 2007–09 Great Financial Crisis), illustrating the empirical inverse relationship between the output gap and unemployment.

                    **2. Counter-Cyclical Monetary Policy Response (Taylor Rule):**
                    The Federal Reserve systematically responds to recessionary demand shocks by lowering the Federal Funds Rate (often to the Effective Lower Bound of 0.0–0.25%, as observed in 2008 and 2020) to stimulate credit creation, lower corporate borrowing costs, and revive aggregate demand.

                    **3. Demand-Driven Disinflation vs. Supply Shocks:**
                    In demand-deficiency recessions (such as 2001 and 2008), inflation rates decelerate significantly as aggregate spending contracts. In contrast, during supply-shock recessions (such as the 1973–75 and 1980 oil crises), negative aggregate supply shifts generated simultaneous output contraction and high inflation (stagflation).

                    **4. Non-Causality Disclaimer:**
                    *These statistics represent historical descriptive associations across classified business cycle regimes. In econometric analysis, business cycle classifications do not imply that recessions isolatedly 'cause' indicator changes; rather, both regimes and indicator shifts are jointly determined by endogenous economic dynamics and exogenous macroeconomic shocks.*
                    """
                )

        else:
            # India Framework
            with st.spinner("Loading authentic Indian national accounts and macroeconomic indicators..."):
                idc = IndiaDataClient()
                df_ind_gdp, g_live, g_note = idc.fetch_rbi_real_gdp_quarterly()
                df_ind_cpi, c_live, c_note = idc.fetch_rbi_cpi_monthly()
                df_ind_iip, i_live, i_note = idc.fetch_rbi_iip_monthly()
                df_ind_wacr, w_live, w_note = idc.fetch_rbi_wacr_monthly()

                df_ind_summary, df_ind_episodes = compute_india_slowdown_statistics(
                    df_gdp=df_ind_gdp,
                    df_cpi=df_ind_cpi,
                    df_iip=df_ind_iip,
                    df_wacr=df_ind_wacr,
                )

            col_chart, col_prov = st.columns([0.74, 0.26])
            with col_chart:
                fig_ind_regime = plot_regime_comparison_bars(
                    df_ind_summary,
                    title="Indian Macroeconomic Indicators: Trend Growth vs. Analytical Slowdowns",
                    is_india=True,
                )
                st.plotly_chart(fig_ind_regime, use_container_width=True)
            with col_prov:
                render_data_provenance_card(
                    col=col_prov,
                    title="India Analytical Slowdown Framework",
                    source_api="Reserve Bank of India DBIE & MoSPI",
                    api_key_status="Authentic Live Data Mirror" if g_live else "Verified RBI DBIE Benchmark",
                    series_code="Quarterly Real GDP (qtr_gdp_mrkt_prc_rn)",
                    frequency="Quarterly (2011–2024)",
                    currency_unit="Growth Rate (% YoY)",
                    badge_type="live" if g_live else "demo",
                    badge_text="LIVE RBI DBIE" if g_live else "RBI BENCHMARK",
                    notes="Analytical Slowdown Rule: ≥ 2 consecutive quarters of Real GDP YoY growth below 5.0% or negative (contraction)."
                )

            st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:16px; margin-bottom:8px;'>1. INDICATOR BEHAVIOR ACROSS TREND GROWTH VS. ANALYTICAL SLOWDOWNS</div>", unsafe_allow_html=True)
            st.dataframe(df_ind_summary, use_container_width=True, hide_index=True)

            st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:20px; margin-bottom:8px;'>2. DOCUMENTED INDIAN ANALYTICAL SLOWDOWN EPISODES</div>", unsafe_allow_html=True)
            st.dataframe(df_ind_episodes, use_container_width=True, hide_index=True)

            with st.expander("Methodological Distinction: Emerging Market Growth Slowdowns vs. US NBER Recessions"):
                st.markdown(
                    """
                    **1. Absence of an Official Recession Committee in India:**
                    Unlike the United States (where the NBER Business Cycle Dating Committee dates peaks and troughs based on broad-based economic contraction), India has no official government or academic recession-dating committee. 

                    **2. Growth Slowdown vs. Absolute Output Contraction:**
                    In a high-growth emerging economy with a trend potential growth rate between 6.0% and 7.0%, economic stress often manifests not as negative GDP growth (absolute contraction), but as a **growth slowdown** (e.g. GDP expanding at only 3.5%–4.5%). Because the workforce grows rapidly, a decelerating growth rate fails to absorb new labor market entrants, creating labor slack similar to an advanced-economy recession.

                    **3. Documented Analytical Slowdown Episodes:**
                    - **2012–13 Twin Balance Sheet Stress:** Deceleration to 4.5%–4.9% driven by corporate debt overhang, stressed public-sector bank non-performing assets (NPAs), and stalled infrastructure investment.
                    - **2019–20 NBFC Liquidity Crunch:** Structural deceleration down to 3.1% in Q4 FY20, triggered by shadow banking liquidity freeze following the IL&FS default and muted private capital expenditure.
                    - **2020 COVID-19 Lockdown Contraction:** The only technical economic contraction in modern Indian quarterly national accounts (-23.1% in Q1 FY21, -6.6% in Q2 FY21).

                    **4. Non-Causality Disclaimer:**
                    *Analytical slowdown classifications are descriptive statistical categories derived from observed GDP series; they do not imply that slowdowns cause specific inflation or monetary rate changes.*
                    """
                )

    with tab_decomposition:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:18px 22px; margin-bottom:16px;">
                <div style="font-size:18px; font-weight:800; color:#0F172A; margin-bottom:4px;">Inflation Trend Decomposition & Time-Series Analytics</div>
                <div style="font-size:13px; color:#475569; line-height:1.55;">
                    Decomposes headline Consumer Price Index (CPI) inflation into underlying <b>Trend (2×12 Centered Moving Average)</b>, <b>Seasonal Cycle (normalized 12-month calendar factor)</b>, and <b>Residual Irregular Variations (noise & supply shocks)</b> using strictly validated contiguous monthly observations. Differentiates clearly between Index Level, Month-on-Month (MoM) %, and Year-on-Year (YoY) % inflation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        infl_choice = st.selectbox(
            "Select Inflation Series & Scope:",
            [
                "United States: CPI-U Headline (FRED)",
                "India: All-India Combined CPI (RBI DBIE / MoSPI)",
                "India: State-Level CPI Inflation Comparison (RBI DBIE)",
            ],
            key="infl_decomp_choice",
        )

        if "United States" in infl_choice:
            df_cpi_us = df_filtered[["date", "CPIAUCSL"]].dropna().copy().sort_values("date").reset_index(drop=True)
            is_contig, contig_msg, missing_m = validate_monthly_continuity(df_cpi_us, "date")

            col_val, col_meta = st.columns([0.65, 0.35])
            with col_val:
                if is_contig:
                    st.success(f"✓ {contig_msg}")
                else:
                    st.warning(f"⚠ {contig_msg}")
            with col_meta:
                st.caption("Frequency: Strictly Monthly | Base: 1982-1984=100 | Source: BLS / FRED")

            df_cpi_calc = calculate_mom_yoy_inflation(df_cpi_us, cpi_col="CPIAUCSL", date_col="date")
            latest_row = df_cpi_calc.iloc[-1]

            k1, k2, k3, k4 = st.columns(4)
            render_kpi(k1, "CPI Index Level", f"{latest_row['CPIAUCSL']:.2f}", "Basket level (1982-84=100)", freq_badge="Level")
            render_kpi(k2, "MoM Inflation Rate", f"{latest_row['inflation_mom']:.2f}%", "1-month price change", delta_val=latest_row['inflation_mom'], freq_badge="Monthly")
            render_kpi(k3, "YoY Inflation Rate", f"{latest_row['inflation_yoy']:.2f}%", "Standard headline benchmark", delta_val=latest_row['inflation_yoy'], freq_badge="Annualized YoY")
            render_kpi(k4, "Annualized MoM Rate", f"{latest_row['inflation_mom_annualized']:.2f}%", "Compound monthly run-rate", freq_badge="Compounded")

            df_peaks, df_troughs = detect_inflation_turning_points(df_cpi_calc, col="inflation_yoy", date_col="date", window=7)
            fig_turning = plot_inflation_turning_points(
                df_cpi_calc, df_peaks, df_troughs,
                title="US Headline CPI YoY Inflation: Turning Points (Peaks & Troughs)",
            )
            st.plotly_chart(fig_turning, use_container_width=True)

            if is_contig and len(df_cpi_calc.dropna(subset=["inflation_yoy"])) >= 24:
                decomp = decompose_monthly_inflation_classical(
                    df_cpi_calc["inflation_yoy"].dropna(),
                    df_cpi_calc.dropna(subset=["inflation_yoy"])["date"],
                    freq=12,
                )
                fig_decomp = plot_inflation_decomposition(
                    decomp,
                    title="US CPI Inflation Decomposition: Trend, 12-Month Seasonality & Residual",
                    units="Percent YoY (%)",
                )
                st.plotly_chart(fig_decomp, use_container_width=True)

                col_shares, col_factors = st.columns([0.4, 0.6])
                with col_shares:
                    st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-bottom:8px;'>Variance Contribution Shares</div>", unsafe_allow_html=True)
                    v_shares = decomp.get("variance_shares", {})
                    st.dataframe(pd.DataFrame([
                        {"Component": "Long-Term Trend (T)", "Variance Explained": f"{v_shares.get('trend_share', 0.0):.2f}%", "Role": "Macroeconomic aggregate demand & monetary drift"},
                        {"Component": "12-Month Seasonality (S)", "Variance Explained": f"{v_shares.get('seasonal_share', 0.0):.2f}%", "Role": "Recurring annual weather, fuel, and holiday patterns"},
                        {"Component": "Residual Irregular (R)", "Variance Explained": f"{v_shares.get('residual_share', 0.0):.2f}%", "Role": "Unanticipated supply shocks, geopolitical events, noise"},
                    ]), use_container_width=True, hide_index=True)

                with col_factors:
                    st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-bottom:8px;'>Normalized Monthly Seasonal Factors (% Deviation)</div>", unsafe_allow_html=True)
                    s_dict = decomp.get("seasonal_factors", {})
                    df_s = pd.DataFrame([{"Month": m, "Seasonal Factor (% pt)": f"{v:+.3f}%"} for m, v in s_dict.items()])
                    st.dataframe(df_s.T, use_container_width=True)

            with st.expander("Pedagogical Note: CPI Level vs. MoM % vs. YoY % Inflation"):
                st.markdown(
                    """
                    **1. CPI Index Level (Price Basket):**
                    Measures the nominal dollar cost of a fixed consumer basket relative to a base period (1982–1984 = 100 for the US). The index level generally trends upward over time due to positive long-term inflation. It is not an inflation rate.

                    **2. Month-on-Month (MoM) Inflation (%):**
                    $$\\pi_{t}^{\\text{MoM}} = \\left( \\frac{\\text{CPI}_t - \\text{CPI}_{t-1}}{\\text{CPI}_{t-1}} \\right) \\times 100$$
                    Captures short-term monthly momentum. However, unannualized MoM figures are susceptible to high-frequency noise and weather-related fluctuations.

                    **3. Year-on-Year (YoY) Headline Inflation (%):**
                    $$\\pi_{t}^{\\text{YoY}} = \\left( \\frac{\\text{CPI}_t - \\text{CPI}_{t-12}}{\\text{CPI}_{t-12}} \\right) \\times 100$$
                    The official headline inflation benchmark monitored by central banks. Comparing against the identical calendar month 12 months prior eliminates predictable annual seasonality without requiring statistical seasonal adjustment.
                    """
                )

        elif "All-India Combined" in infl_choice:
            with st.spinner("Fetching authentic All-India Combined CPI series from RBI DBIE..."):
                idc = IndiaDataClient()
                df_ind_cpi_raw, c_live, c_note = idc.fetch_rbi_cpi_monthly()

            df_ind_cpi_calc = calculate_mom_yoy_inflation(df_ind_cpi_raw, cpi_col="cpi_index", date_col="date")
            is_contig, contig_msg, _ = validate_monthly_continuity(df_ind_cpi_calc, "date")

            col_val, col_meta = st.columns([0.65, 0.35])
            with col_val:
                st.success(f"✓ {contig_msg}")
            with col_meta:
                st.caption(f"Status: {c_note}")

            latest_row = df_ind_cpi_calc.iloc[-1]
            k1, k2, k3, k4 = st.columns(4)
            render_kpi(k1, "All-India CPI Level", f"{latest_row['cpi_index']:.2f}", "Combined Base 2012=100", freq_badge="Level")
            render_kpi(k2, "MoM Inflation Rate", f"{latest_row['inflation_mom']:.2f}%", "1-month price change", delta_val=latest_row['inflation_mom'], freq_badge="Monthly")
            render_kpi(k3, "YoY Headline Inflation", f"{latest_row['inflation_yoy']:.2f}%", "RBI 4±2% Tolerance Band", delta_val=latest_row['inflation_yoy'], freq_badge="YoY Combined")
            render_kpi(k4, "Annualized MoM Run-Rate", f"{latest_row['inflation_mom_annualized']:.2f}%", "Compounded annual run-rate", freq_badge="Run-Rate")

            df_peaks, df_troughs = detect_inflation_turning_points(df_ind_cpi_calc, col="inflation_yoy", date_col="date", window=6)
            fig_turning = plot_inflation_turning_points(
                df_ind_cpi_calc, df_peaks, df_troughs,
                title="India CPI Combined YoY Inflation: Historical Turning Points",
            )
            st.plotly_chart(fig_turning, use_container_width=True)

            decomp = decompose_monthly_inflation_classical(
                df_ind_cpi_calc["inflation_yoy"].dropna(),
                df_ind_cpi_calc.dropna(subset=["inflation_yoy"])["date"],
                freq=12,
            )
            fig_decomp = plot_inflation_decomposition(
                decomp,
                title="India CPI Inflation Decomposition: Trend, Harvest Seasonality & Residual",
                units="Percent YoY (%)",
            )
            st.plotly_chart(fig_decomp, use_container_width=True)

            col_shares, col_factors = st.columns([0.4, 0.6])
            with col_shares:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-bottom:8px;'>Variance Contribution Shares</div>", unsafe_allow_html=True)
                v_shares = decomp.get("variance_shares", {})
                st.dataframe(pd.DataFrame([
                    {"Component": "Trend Component (T)", "Variance Explained": f"{v_shares.get('trend_share', 0.0):.2f}%", "Role": "Macroeconomic core demand & underlying cost-push"},
                    {"Component": "Seasonal Cycle (S)", "Variance Explained": f"{v_shares.get('seasonal_share', 0.0):.2f}%", "Role": "Monsoon & agricultural harvest cycles (Kharif/Rabi)"},
                    {"Component": "Residual / Shocks (R)", "Variance Explained": f"{v_shares.get('residual_share', 0.0):.2f}%", "Role": "Vegetable supply shocks (tomato/onion), fuel tax adjustments"},
                ]), use_container_width=True, hide_index=True)

            with col_factors:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-bottom:8px;'>Monthly Seasonal Swings (% Deviation from Annual Mean)</div>", unsafe_allow_html=True)
                s_dict = decomp.get("seasonal_factors", {})
                df_s = pd.DataFrame([{"Month": m, "Seasonal Factor (% pt)": f"{v:+.3f}%"} for m, v in s_dict.items()])
                st.dataframe(df_s.T, use_container_width=True)

            with st.expander("Economic Analysis: Food Basket Weight & Agricultural Seasonality in India"):
                st.markdown(
                    """
                    **Food and Beverages Weight in India's CPI (45.86%):**
                    Unlike advanced economies (where food constitutes ~14% of the US CPI basket), food and beverages comprise **45.86%** of the All-India Consumer Price Index basket. Consequently, agricultural seasonality exerts a substantial influence on headline inflation.

                    - **Summer/Monsoon Surge (June–September):** Perishable vegetable supplies dwindle prior to the Kharif harvest, causing seasonal positive deviations.
                    - **Winter Disinflation (December–February):** Fresh market arrivals of winter crops (Rabi harvest) lead to sharp seasonal declines in food prices, producing predictable downward pressure on headline CPI.
                    - **Policy Implications for RBI:** The Monetary Policy Committee (MPC) looks through transient seasonal food price spikes unless second-round effects spread into core goods and services.
                    """
                )

        else:
            with st.spinner("Fetching State-Level CPI from RBI DBIE (cpi_ruc_st_rn)..."):
                isdc = IndiaStateDataClient()
                df_st_cpi, st_live, st_note = isdc.fetch_state_cpi_inflation()

            col_h, col_p = st.columns([0.74, 0.26])
            with col_h:
                fig_st_bar = plot_state_ranking_barchart(
                    df_st_cpi,
                    metric_col="cpi_inflation_yoy",
                    title=f"State-Level CPI Combined YoY Inflation (% p.a. — {df_st_cpi['reference_period'].iloc[0]})",
                    value_suffix="%",
                )
                st.plotly_chart(fig_st_bar, use_container_width=True)
            with col_p:
                render_data_provenance_card(
                    col=col_p,
                    title="State-Level CPI Combined",
                    source_api="Reserve Bank of India DBIE",
                    api_key_status=st_note,
                    series_code="real_sector.cpi_ruc_st_rn",
                    frequency="Monthly State Extracts (Base 2012=100)",
                    currency_unit="Inflation Rate (% YoY)",
                    badge_type="live" if st_live else "demo",
                    badge_text="LIVE RBI DBIE" if st_live else "RBI BENCHMARK",
                    notes="Calculated from actual 12-month lagged state price indexes across rural + urban state baskets."
                )

            max_st = df_st_cpi.loc[df_st_cpi["cpi_inflation_yoy"].idxmax()]
            min_st = df_st_cpi.loc[df_st_cpi["cpi_inflation_yoy"].idxmin()]
            nat_avg = df_st_cpi.loc[df_st_cpi["state"] == "All-India", "cpi_inflation_yoy"].values
            nat_val = nat_avg[0] if len(nat_avg) > 0 else df_st_cpi["cpi_inflation_yoy"].mean()
            iqr = df_st_cpi["cpi_inflation_yoy"].quantile(0.75) - df_st_cpi["cpi_inflation_yoy"].quantile(0.25)

            sk1, sk2, sk3, sk4 = st.columns(4)
            render_kpi(sk1, "Highest Inflation State", f"{max_st['cpi_inflation_yoy']:.2f}%", f"{max_st['state']}", freq_badge="Peak State")
            render_kpi(sk2, "Lowest Inflation State", f"{min_st['cpi_inflation_yoy']:.2f}%", f"{min_st['state']}", freq_badge="Trough State")
            render_kpi(sk3, "All-India Headline Rate", f"{nat_val:.2f}%", "Combined national benchmark", freq_badge="National")
            render_kpi(sk4, "Interstate Dispersion (IQR)", f"{iqr:.2f}% pts", "75th - 25th percentile spread", freq_badge="Dispersion")

            st.dataframe(df_st_cpi.sort_values("cpi_inflation_yoy", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)

    with tab_global_wb:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:18px 22px; margin-bottom:16px;">
                <div style="font-size:18px; font-weight:800; color:#0F172A; margin-bottom:4px;">Cross-Country Global Macroeconomic Comparison</div>
                <div style="font-size:13px; color:#475569; line-height:1.55;">
                    Official cross-country comparative macroeconomic intelligence querying <b>World Bank Indicators API V2</b>. Evaluates national time series across verified common calendar years, ensuring unbiased international league table rankings across <b>GDP Growth (<code>NY.GDP.MKTP.KD.ZG</code>)</b>, <b>Consumer Price Inflation (<code>FP.CPI.TOTL.ZG</code>)</b>, and <b>Unemployment (<code>SL.UEM.TOTL.ZS</code>)</b> without requiring API keys.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        wb_meta_map = {
            "NY.GDP.MKTP.KD.ZG": {"name": "Real GDP Growth", "unit": "Annual %", "desc": "Annual percentage growth rate of GDP at market prices based on constant local currency."},
            "FP.CPI.TOTL.ZG": {"name": "Consumer Price Inflation", "unit": "Annual %", "desc": "Annual percentage change in the cost to the average consumer of acquiring a basket of goods and services."},
            "SL.UEM.TOTL.ZS": {"name": "Unemployment Rate", "unit": "% of Total Labor Force", "desc": "Share of labor force that is without work but available and seeking employment (modeled ILO estimate)."},
        }

        wb_col1, wb_col2, wb_col3 = st.columns([0.35, 0.40, 0.25])
        with wb_col1:
            sel_wb_ind_code = st.selectbox(
                "Select Macro Indicator:",
                options=list(wb_meta_map.keys()),
                format_func=lambda x: f"{wb_meta_map[x]['name']} ({x})",
                key="wb_ind_code_sel",
            )
        with wb_col2:
            sel_wb_countries = st.multiselect(
                "Select Economies to Compare:",
                options=list(SUPPORTED_COUNTRIES.keys()),
                default=["IND", "USA", "GBR", "DEU", "JPN", "CHN"],
                format_func=lambda x: f"{x} — {SUPPORTED_COUNTRIES[x]}",
                key="wb_countries_multi",
            )
        with wb_col3:
            wb_year_range = st.slider("Historical Window:", min_value=1995, max_value=2023, value=(2005, 2023), step=1, key="wb_yr_slider")

        if not sel_wb_countries:
            st.info("Please select at least two countries to compare.")
        else:
            with st.spinner("Fetching and aligning multi-country World Bank series across common years..."):
                wbc = WorldBankClient()
                df_wb_matrix, common_years, coverage_summary, wb_live, wb_status = wbc.fetch_multi_country_indicator(
                    countries=sel_wb_countries,
                    indicator_code=sel_wb_ind_code,
                    start_year=wb_year_range[0],
                    end_year=wb_year_range[1],
                )

            ind_meta = wb_meta_map[sel_wb_ind_code]

            col_chart, col_prov = st.columns([0.74, 0.26])
            with col_chart:
                fig_wb_multi = plot_world_bank_multi_country(
                    df_wb_matrix,
                    indicator_name=ind_meta["name"],
                    units=ind_meta["unit"],
                    common_years=common_years,
                )
                st.plotly_chart(fig_wb_multi, use_container_width=True)
            with col_prov:
                render_data_provenance_card(
                    col=col_prov,
                    title="World Bank Open Data V2",
                    source_api="World Bank Indicators API V2",
                    api_key_status="Unauthenticated Open Access",
                    series_code=sel_wb_ind_code,
                    frequency="Annual Official Historical Observations",
                    currency_unit=f"Units: {ind_meta['unit']}",
                    badge_type="wb",
                    badge_text="WORLD BANK V2",
                    notes=f"{wb_status} Shaded band denotes common calendar years where all selected economies have verified observations."
                )

            if common_years:
                latest_common_yr = max(common_years)
                df_rank = wbc.fetch_cross_sectional_ranking(
                    countries=sel_wb_countries,
                    indicator_code=sel_wb_ind_code,
                    target_year=latest_common_yr,
                )

                st.markdown(f"<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:16px; margin-bottom:8px;'>1. CROSS-COUNTRY LEAGUE TABLE (LATEST COMMON CALENDAR YEAR: {latest_common_yr})</div>", unsafe_allow_html=True)
                col_bar_l, col_tbl_l = st.columns([0.55, 0.45])
                with col_bar_l:
                    fig_league = plot_world_bank_league_table(df_rank, indicator_name=ind_meta["name"], units=ind_meta["unit"])
                    st.plotly_chart(fig_league, use_container_width=True)
                with col_tbl_l:
                    st.dataframe(
                        df_rank[["rank", "country", "country_code", "value", "observation_year"]].rename(columns={
                            "rank": "Rank", "country": "Country", "country_code": "ISO Code",
                            "value": f"{ind_meta['name']} ({ind_meta['unit']})",
                            "observation_year": "Year",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )

            st.markdown("<div style='font-size:12px; font-weight:700; color:#0F172A; text-transform:uppercase; margin-top:20px; margin-bottom:8px;'>2. DATA COVERAGE & MISSING OBSERVATION REPORT</div>", unsafe_allow_html=True)
            cov_rows = []
            for c, info in coverage_summary.items():
                cov_rows.append({
                    "Economy": info["name"],
                    "ISO Code": info["code"],
                    "Available Years": info["available_years"],
                    "Missing Years": info["missing_years"],
                    "Coverage %": f"{info['coverage_pct']:.1f}%",
                    "Period Range": f"{info['start_year']} – {info['latest_year']}" if info['start_year'] else "N/A",
                    "Latest Value": f"{info['latest_val']:.2f} {ind_meta['unit']}" if info['latest_val'] is not None else "N/A",
                })
            st.dataframe(pd.DataFrame(cov_rows), use_container_width=True, hide_index=True)

            with st.expander("Methodological Principles & World Bank Indicator Limitations"):
                st.markdown(
                    f"""
                    **1. Concept Definition ({ind_meta['name']}):**
                    {ind_meta['desc']}

                    **2. Why Indicators are Evaluated Independently:**
                    Combining real output growth, inflation, and unemployment into an arbitrary single score obscures the distinct macroeconomic trade-offs described by Okun's Law and the Phillips Curve. For instance, high GDP growth accompanying double-digit inflation indicates economic overheating, whereas high GDP growth with anchored inflation signals sustainable potential output expansion.

                    **3. Common-Year Alignment:**
                    Cross-country comparisons are conducted over **common calendar years** (highlighted in grey) to prevent sample selection bias where lagging reporting schedules for certain developing countries distort ranking positions.

                    **4. Reporting Limitations:**
                    World Bank series are compiled on an annual historical frequency from official national statistical agencies and international organizations (such as the ILO). Observations typically lag high-frequency domestic data by 6 to 18 months.
                    """
                )

    with tab_single_deep:
        series_options = {
            "GDPC1": ("Real Gross Domestic Product", "Billions of Chained Rupees (₹B, @ ₹83/USD)", "Quarterly"),
            "CPIAUCSL": ("Consumer Price Index (CPI-U)", "Index 1982-1984=100", "Monthly"),
            "inflation_yoy": ("Year-over-Year Inflation Rate", "Percent YoY", "Monthly derived"),
            "UNRATE": ("Civilian Unemployment Rate", "Percent of Labor Force", "Monthly"),
            "FEDFUNDS": ("Effective Federal Funds Rate", "Percent Annualized", "Monthly"),
            "GS10": ("10-Year Treasury Yield", "Percent Constant Maturity", "Monthly"),
            "misery_index": ("Misery Index (Inflation + Unemployment)", "Percent Points", "Monthly derived"),
            "real_interest_rate": ("Approximate Real Rate (Fed Funds − Inflation)", "Percent Annualized", "Monthly derived"),
        }

        col_sel, col_stats = st.columns([0.4, 0.6])
        with col_sel:
            chosen_series = st.selectbox(
                "Select Series:",
                options=list(series_options.keys()),
                format_func=lambda x: f"{series_options[x][0]} ({series_options[x][1]})",
            )

        s_name, s_units, s_freq = series_options[chosen_series]
        s_data = df_filtered[chosen_series].dropna()

        with col_stats:
            if not s_data.empty:
                st.markdown(
                    f"""
                    <div style="display:flex; gap:16px; margin-top:24px;">
                        <div><span style="font-size:11px; color:#64748B;">LATEST:</span> <b>{s_data.iloc[-1]:.2f}</b></div>
                        <div><span style="font-size:11px; color:#64748B;">MEAN:</span> <b>{s_data.mean():.2f}</b></div>
                        <div><span style="font-size:11px; color:#64748B;">MIN:</span> <b>{s_data.min():.2f}</b></div>
                        <div><span style="font-size:11px; color:#64748B;">MAX:</span> <b>{s_data.max():.2f}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        fig_single = go.Figure()
        fig_single.add_trace(
            go.Scatter(
                x=df_filtered["date"],
                y=df_filtered[chosen_series],
                name=s_name,
                line=dict(color="#FF5200", width=2.5),
                hovertemplate=f"{s_name}: %{{y:.2f}} {s_units}<extra></extra>",
            )
        )
        if len(df_filtered) > 12:
            fig_single.add_trace(
                go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered[chosen_series].rolling(12).mean(),
                    name="12-Month Moving Average",
                    line=dict(color="#0F172A", width=1.5, dash="dash"),
                    hovertemplate="12M Avg: %{y:.2f}<extra></extra>",
                )
            )

        # Add shaded NBER recession bands
        add_nber_recession_bands(fig_single, df_filtered, opacity=0.20)

        apply_terminal_theme(fig_single, height=450, title=f"{s_name} ({s_units}) — {s_freq} with NBER Recession Shading")
        
        col_c, col_p = st.columns([0.76, 0.24])
        with col_c:
            st.plotly_chart(fig_single, use_container_width=True)
        with col_p:
            api_status_str = "Authenticated via FRED_API_KEY in .env" if is_live_data else "Demonstration Snapshot (1990–2024)"
            b_type = "live" if is_live_data else "demo"
            b_txt = "LIVE FRED" if is_live_data else "DEMO SNAPSHOT"
            curr_desc = "Indian Rupees (₹B)" if chosen_series == "GDPC1" else f"Reporting Unit: {s_units}"
            render_data_provenance_card(
                col=col_p,
                title=f"FRED: {s_name}",
                source_api="Federal Reserve Bank of St. Louis (FRED)",
                api_key_status=api_status_str,
                series_code=chosen_series,
                frequency=s_freq,
                currency_unit=curr_desc,
                badge_type=b_type,
                badge_text=b_txt,
                notes=f"Calculated over selected range ({date_range[0]}–{date_range[1]}). Shaded grey bands indicate NBER recessions."
            )

    with tab_data_table:
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:8px;'>OBSERVATION DATA MATRIX (CHRONOLOGICAL)</div>", unsafe_allow_html=True)
        display_columns = [
            "date", "GDPC1", "CPIAUCSL", "inflation_yoy", "UNRATE",
            "FEDFUNDS", "GS10", "misery_index", "real_interest_rate",
        ]
        available_cols = [c for c in display_columns if c in df_filtered.columns]
        st.dataframe(
            df_filtered[available_cols].sort_values("date", ascending=False).reset_index(drop=True),
            use_container_width=True,
            height=450,
        )


# ==============================================================================
# 3. INDIAN STATE-LEVEL ECONOMIC INTELLIGENCE & STRESS DASHBOARD
# ==============================================================================
elif selected_page == "State Intelligence":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_state_intelligence", on_click=navigate_to, args=(None,))

    # Hero Banner
    st.markdown(
        """
        <div style="background:linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 50%, #DCFCE7 100%); border:1px solid #BBF7D0; border-radius:16px; padding:22px 26px; margin-bottom:20px; box-shadow:0 4px 18px rgba(22,163,74,0.04);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#0F172A; letter-spacing:-0.03em; margin-bottom:4px;">Indian State-Level Economic Intelligence & Stress Dashboard</div>
                    <div style="font-size:13.5px; color:#475569; max-width:880px; line-height:1.55;">
                        Official empirical statistics from the <b>Reserve Bank of India</b> (Handbook of Statistics & State Finances: A Study of Budgets) and <b>MoSPI</b> (Periodic Labour Force Survey). Evaluating real and nominal state domestic output, per-capita incomes, labour market slack, and regional economic stress across Indian States and Union Territories.
                    </div>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <span class="badge-live-pill"><span class="pulse-dot-live"></span> RBI DBIE & MoSPI PLFS</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load State Intelligence Dataset
    try:
        state_data_bundle = load_state_intelligence_data()
        df_snapshot = state_data_bundle["df_snapshot"]
        df_trends = state_data_bundle["df_trends"]
        state_provenance = state_data_bundle["provenance"]
    except Exception as exc:
        st.error(f"Error loading state economic intelligence data: {exc}")
        st.stop()

    # Calculate State Economic Stress Index
    df_stress_ranked, stress_results = compute_state_economic_stress_index(df_snapshot)

    # State Module Sub-Navigation
    tab_profile, tab_rankings, tab_stress = st.tabs([
        "State Comparison & Profiles",
        "National State Rankings",
        "Economic Stress Dashboard",
    ])

    # --------------------------------------------------------------------------
    # TAB 1: STATE COMPARISON & PROFILES
    # --------------------------------------------------------------------------
    with tab_profile:
        st.markdown(
            """
            <div style="font-size:11px; font-weight:700; color:#15803D; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
                REGIONAL ECONOMIC ACCOUNTS & COMPARATIVE TIMELINES
            </div>
            """,
            unsafe_allow_html=True,
        )

        all_states = sorted(list(INDIAN_STATES_METADATA.keys()))
        col_sel_s, col_mode = st.columns([0.65, 0.35])

        with col_sel_s:
            selected_states = st.multiselect(
                "Select States to Analyze & Compare:",
                options=all_states,
                default=["Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Uttar Pradesh"],
                help="Select one state for a detailed economic profile or multiple states for head-to-head trend comparison.",
            )

        with col_mode:
            compare_metric = st.selectbox(
                "Comparison Metric (for Trends):",
                options=[
                    ("per_capita_real_inr", "Per Capita Real Income (₹ Base 2011-12)", "₹", "RBI Handbook Table 250"),
                    ("per_capita_nominal_inr", "Per Capita Nominal Income (₹ Current Prices)", "₹", "RBI Handbook Table 227"),
                    ("real_growth_yoy", "Real Output Growth (% YoY)", "% YoY", "RBI Handbook Table 66"),
                    ("debt_gsdp_pct", "State Debt Burden (% of GSDP)", "%", "RBI State Finances: A Study of Budgets"),
                    ("plfs_ur", "PLFS Unemployment Rate (%)", "%", "MoSPI PLFS Annual Reports Table 4"),
                    ("plfs_lfpr", "PLFS Labour Force Participation Rate (%)", "%", "MoSPI PLFS Annual Reports Table 1"),
                ],
                format_func=lambda x: x[1],
            )

        if not selected_states:
            st.info("Please select at least one state from the dropdown menu to inspect economic observations.")
        elif len(selected_states) == 1:
            # Single State Deep-Dive Profile
            sname = selected_states[0]
            s_snap = df_snapshot[df_snapshot["state"] == sname]
            if not s_snap.empty:
                s_row = s_snap.iloc[0]
                meta = INDIAN_STATES_METADATA.get(sname, {})

                st.markdown(
                    f"""
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:12px 18px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:18px; font-weight:800; color:#0F172A;">{sname}</span>
                            <span style="font-size:12px; color:#64748B; margin-left:8px;">Capital: <b>{meta.get('capital', 'N/A')}</b> | Region: <b>{meta.get('region', 'N/A')}</b> | RBI Code: <code>{meta.get('code', 'N/A')}</code></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # 6 Elevated KPI Cards
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                pc_real_val = s_row["per_capita_real_inr"]
                render_kpi(
                    c1,
                    title="Real Per Capita Income",
                    value_str=f"₹{pc_real_val:,.0f}" if pd.notna(pc_real_val) else "N/A",
                    sub_str=f"Base 2011-12 ({s_row['per_capita_real_yr']})",
                    freq_badge="Annual FY",
                )
                pc_nom_val = s_row["per_capita_nominal_inr"]
                render_kpi(
                    c2,
                    title="Nominal Per Capita Income",
                    value_str=f"₹{pc_nom_val:,.0f}" if pd.notna(pc_nom_val) else "N/A",
                    sub_str=f"Current Prices ({s_row['per_capita_nominal_yr']})",
                    freq_badge="Annual FY",
                )
                rg_val = s_row["real_growth_yoy"]
                render_kpi(
                    c3,
                    title="Real Output Growth",
                    value_str=f"{rg_val:.2f}%" if pd.notna(rg_val) else "N/A",
                    sub_str=f"YoY Constant ({s_row['growth_ref_yr']})",
                    delta_val=rg_val,
                    freq_badge="Annual FY",
                )
                cpi_val = s_row["cpi_inflation_yoy"]
                render_kpi(
                    c4,
                    title="State CPI Inflation",
                    value_str=f"{cpi_val:.2f}%" if pd.notna(cpi_val) else "N/A",
                    sub_str=f"Combined ({s_row['cpi_ref_period']})",
                    delta_val=cpi_val,
                    invert_color=True,
                    freq_badge="Monthly YoY",
                )
                ur_val = s_row["plfs_ur"]
                render_kpi(
                    c5,
                    title="PLFS Unemployment Rate",
                    value_str=f"{ur_val:.2f}%" if pd.notna(ur_val) else "N/A",
                    sub_str=f"Usual Status 15+ ({s_row['plfs_ref_yr']})",
                    delta_val=ur_val,
                    invert_color=True,
                    freq_badge="Survey Round",
                )
                debt_val = s_row["debt_gsdp_pct"]
                render_kpi(
                    c6,
                    title="Debt Burden (% GSDP)",
                    value_str=f"{debt_val:.1f}%" if pd.notna(debt_val) else "N/A",
                    sub_str=f"Outstanding Liabilities ({s_row['debt_ref_yr']})",
                    delta_val=debt_val,
                    invert_color=True,
                    freq_badge="Annual FY",
                )

                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

                col_chart, col_prov = st.columns([0.74, 0.26])
                with col_chart:
                    fig_trend = plot_state_historical_trends(
                        df_trends=df_trends,
                        states_selected=[sname],
                        metric_col=compare_metric[0],
                        metric_name=compare_metric[1],
                        unit=compare_metric[2],
                        source_name=compare_metric[3],
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

                with col_prov:
                    render_data_provenance_card(
                        col=col_prov,
                        title=f"State Accounts: {sname}",
                        source_api="Reserve Bank of India (DBIE) & MoSPI PLFS",
                        api_key_status="Open Access DBIE Mirror & MoSPI Reports",
                        series_code=f"HBS-227/250 & {compare_metric[0]}",
                        frequency="Annual Financial Years (Base 2011-12)",
                        currency_unit=compare_metric[2],
                        badge_type="live",
                        badge_text="LIVE STATE DATA",
                        notes=(
                            f"Region: {meta.get('region', 'N/A')}. Real metrics strip out price variations "
                            "using constant 2011-12 base prices to measure true volume expansion."
                        ),
                    )

                # Nominal vs Real Explanation
                st.markdown(
                    """
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px 20px; margin-top:14px;">
                        <div style="font-size:12px; font-weight:800; color:#15803D; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">
                            METHODOLOGICAL DISTINCTION: NOMINAL VS. REAL STATE ACCOUNTS
                        </div>
                        <div style="font-size:13px; color:#334155; line-height:1.6;">
                            • <b>Nominal GSDP / NSDP (Current Prices):</b> Evaluates output at prevailing prices of each respective reporting year. Reflects both physical production growth and price inflation.<br>
                            • <b>Real GSDP / NSDP (Constant 2011-12 Prices):</b> Deflates current price estimates using the constant base year (2011-12) price structure. Eliminates inflation distortions to reveal genuine physical economic growth and purchasing power.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            # Multi-State Comparison Mode
            st.markdown(f"Comparing <b>{len(selected_states)} states</b> on <b>{compare_metric[1]}</b>:")
            col_chart, col_prov = st.columns([0.74, 0.26])

            with col_chart:
                fig_trend = plot_state_historical_trends(
                    df_trends=df_trends,
                    states_selected=selected_states,
                    metric_col=compare_metric[0],
                    metric_name=compare_metric[1],
                    unit=compare_metric[2],
                    source_name=compare_metric[3],
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            with col_prov:
                render_data_provenance_card(
                    col=col_prov,
                    title="Multi-State Comparison",
                    source_api=compare_metric[3],
                    api_key_status="Open Access DBIE Mirror / MoSPI",
                    series_code=compare_metric[0],
                    frequency="Annual Observation Cadence",
                    currency_unit=compare_metric[2],
                    badge_type="live",
                    badge_text="EMPIRICAL FEED",
                    notes="Harmonized comparison under official Base 2011-12 national accounts guidelines."
                )

            # Comparative Metrics Table for Selected States
            st.markdown("<div style='font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase; margin-top:10px; margin-bottom:6px;'>LATEST COMPARATIVE SUMMARY TABLE</div>", unsafe_allow_html=True)
            comp_sub = df_snapshot[df_snapshot["state"].isin(selected_states)][[
                "state", "region", "per_capita_real_inr", "per_capita_real_yr",
                "real_growth_yoy", "growth_ref_yr", "cpi_inflation_yoy",
                "debt_gsdp_pct", "debt_ref_yr", "plfs_ur", "plfs_ref_yr",
            ]].copy()
            comp_sub.columns = [
                "State", "Region", "Real Per Capita (₹)", "Per Capita Year",
                "Real Growth (%)", "Growth Year", "CPI Inflation (%)",
                "Debt/GSDP (%)", "Debt Year", "PLFS UR (%)", "PLFS Year",
            ]
            st.dataframe(comp_sub.sort_values("Real Per Capita (₹)", ascending=False), width="stretch", hide_index=True)

    # --------------------------------------------------------------------------
    # TAB 2: NATIONAL STATE RANKINGS
    # --------------------------------------------------------------------------
    with tab_rankings:
        st.markdown(
            """
            <div style="font-size:11px; font-weight:700; color:#15803D; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
                CROSS-STATE EMPIRICAL RANKINGS & LEAGUE TABLES
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_r_metric, col_r_region, col_r_top = st.columns([0.45, 0.35, 0.20])
        with col_r_metric:
            rank_metric = st.selectbox(
                "Ranking Indicator:",
                options=[
                    ("per_capita_real_inr", "Per Capita Real Income (₹ Constant 2011-12)", "₹", "RBI Handbook Table 250", "per_capita_real_yr", True, "Blues"),
                    ("per_capita_nominal_inr", "Per Capita Nominal Income (₹ Current Prices)", "₹", "RBI Handbook Table 227", "per_capita_nominal_yr", True, "Greens"),
                    ("real_growth_yoy", "Real Output Growth (% YoY)", "% YoY", "RBI Handbook Table 66", "growth_ref_yr", True, "YlGnBu"),
                    ("cpi_inflation_yoy", "State CPI Inflation (% YoY)", "% YoY", "RBI DBIE Base 2012 Combined", "cpi_ref_period", False, "Reds"),
                    ("plfs_ur", "PLFS Unemployment Rate (%)", "%", "MoSPI PLFS Annual Reports Table 4", "plfs_ref_yr", False, "Oranges"),
                    ("debt_gsdp_pct", "State Debt Burden (% of GSDP)", "%", "RBI State Finances: A Study of Budgets", "debt_ref_yr", False, "Purples"),
                    ("gfd_gsdp_pct", "Gross Fiscal Deficit (% of GSDP)", "%", "RBI State Finances: A Study of Budgets", "debt_ref_yr", False, "YlOrRd"),
                ],
                format_func=lambda x: x[1],
            )

        with col_r_region:
            regions_list = ["All Regions", "Northern", "Southern", "Western", "Eastern", "Central", "North-Eastern", "Union Territories"]
            selected_region = st.selectbox("Filter by Region:", options=regions_list)

        with col_r_top:
            top_n_states = st.selectbox("Display Limit:", options=[None, 10, 15, 20], format_func=lambda x: "All States" if x is None else f"Top {x}")

        # Filter dataset
        df_rank_filtered = df_snapshot.copy()
        if selected_region != "All Regions":
            df_rank_filtered = df_rank_filtered[df_rank_filtered["region"] == selected_region]

        # Render Ranking Bar Chart
        fig_rank = plot_state_ranking_barchart(
            df=df_rank_filtered,
            indicator_col=rank_metric[0],
            indicator_name=rank_metric[1],
            unit=rank_metric[2],
            source_name=rank_metric[3],
            ref_year_col=rank_metric[4],
            top_n=top_n_states,
            ascending=rank_metric[5],
            color_scale=rank_metric[6],
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # Full Ranking Table
        st.markdown("<div style='font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase; margin-top:10px; margin-bottom:6px;'>OFFICIAL OBSERVATION LEAGUE TABLE</div>", unsafe_allow_html=True)
        valid_rank_df = df_rank_filtered.dropna(subset=[rank_metric[0]]).sort_values(rank_metric[0], ascending=not rank_metric[5]).reset_index(drop=True)
        valid_rank_df["Rank"] = range(1, len(valid_rank_df) + 1)

        ref_col = rank_metric[4]
        table_cols = ["Rank", "state", "region", rank_metric[0]]
        if ref_col in valid_rank_df.columns:
            table_cols.append(ref_col)

        display_rank_df = valid_rank_df[table_cols].copy()
        display_rank_df.columns = ["Rank", "State", "Region", f"{rank_metric[1]} ({rank_metric[2]})"] + (["Reference Period"] if ref_col in valid_rank_df.columns else [])
        st.dataframe(display_rank_df, width="stretch", hide_index=True)

    # --------------------------------------------------------------------------
    # TAB 3: ECONOMIC STRESS DASHBOARD
    # --------------------------------------------------------------------------
    with tab_stress:
        st.markdown(
            """
            <div style="font-size:11px; font-weight:700; color:#E11D48; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
                EMPIRICAL STATE ECONOMIC STRESS DASHBOARD & VULNERABILITY INDEX
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Methodology & Disclaimer Explainer Banner
        st.markdown(
            """
            <div style="background:#FFF1F2; border:1.5px solid #FECDD3; border-radius:14px; padding:16px 20px; margin-bottom:18px;">
                <div style="font-size:12px; font-weight:800; color:#BE123C; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">
                    METHODOLOGY & PEDAGOGICAL DISCLAIMER
                </div>
                <div style="font-size:13px; color:#334155; line-height:1.6;">
                    • <b>Documented Normalization (Min-Max Feature Scaling):</b> All indicators are rescaled to a normalized [0, 100] scale. Stress-inducing metrics (Debt/GSDP, PLFS Unemployment, CPI Inflation, Fiscal Deficit) scale positively with higher scores indicating higher stress. Growth indicators scale inversely.<br>
                    • <b>Explicit Weights:</b> Debt Burden (25%), Unemployment (25%), CPI Inflation (20%), Fiscal Deficit (15%), Real Growth (15%).<br>
                    • <b>Strict Handling of Missing Data:</b> No fabricated numbers or national average substitutions are used. Scores are normalized strictly over available empirical components. States with fewer than 3 available components are flagged as <i>'Insufficient Data Coverage'</i> and excluded from league rankings.<br>
                    • <b>Analytical Nature:</b> This is an experimental educational benchmarking tool, <b>NOT an official Government of India, RBI, or MoSPI credit rating or default probability</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Stress Quadrant Plot
        col_quad, col_inspect = st.columns([0.62, 0.38])
        with col_quad:
            fig_quad = plot_stress_quadrant(df_stress_ranked)
            st.plotly_chart(fig_quad, use_container_width=True)

        with col_inspect:
            st.markdown("<div style='font-size:13px; font-weight:700; color:#0F172A; margin-bottom:4px;'>Inspect State Stress Decomposition</div>", unsafe_allow_html=True)
            eligible_states = df_stress_ranked[df_stress_ranked["is_eligible"]]["state"].tolist()
            inspect_state = st.selectbox("Select State to Decompose:", options=eligible_states, index=0)
            fig_decomp = plot_stress_index_breakdown(df_stress_ranked, stress_results, inspect_state)
            st.plotly_chart(fig_decomp, use_container_width=True)

        # Full Ranked Stress Table
        st.markdown("<div style='font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase; margin-top:14px; margin-bottom:6px;'>STATE ECONOMIC STRESS LEADERBOARD (RANKED BY RELATIVE VULNERABILITY)</div>", unsafe_allow_html=True)

        stress_display_df = df_stress_ranked[[
            "stress_rank", "state", "region", "stress_score", "stress_tier",
            "components_count", "debt_gsdp_pct", "plfs_ur", "cpi_inflation_yoy",
            "gfd_gsdp_pct", "real_growth_yoy", "eligibility_note",
        ]].copy()
        stress_display_df.columns = [
            "Rank", "State", "Region", "Stress Score (0-100)", "Vulnerability Tier",
            "Data Coverage", "Debt/GSDP (%)", "PLFS UR (%)", "CPI YoY (%)",
            "GFD/GSDP (%)", "Real Growth (%)", "Methodology Notes",
        ]
        st.dataframe(stress_display_df, width="stretch", hide_index=True)


# ==============================================================================
# PHILLIPS CURVE (INFLATION VS UNEMPLOYMENT EMPIRICAL TRADE-OFF)
# ==============================================================================
elif selected_page == "Phillips Curve":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_phillips", on_click=navigate_to, args=(None,))

    st.markdown(
        """
        <div style="background:linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 50%, #F5F3FF 100%); border:1px solid #E9D5FF; border-radius:16px; padding:22px 26px; margin-bottom:20px; box-shadow:0 4px 18px rgba(147,51,234,0.04);">
            <div style="font-size:24px; font-weight:800; color:#0F172A; letter-spacing:-0.03em; margin-bottom:4px;">Empirical Phillips Curve Analysis</div>
            <div style="font-size:13.5px; color:#475569; max-width:880px; line-height:1.55;">
                Investigates the inverse structural relationship between labor market tightness (Civilian Unemployment Rate, <code>UNRATE</code>) and price acceleration (CPI Inflation Rate YoY, <code>CPIAUCSL</code>) across historical macroeconomic regimes. Features dynamic rolling correlation and empirical OLS slope fitting.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_pc_sel, col_pc_roll = st.columns([0.55, 0.45])
    with col_pc_sel:
        pc_country = st.radio(
            "Select Economy for Phillips Curve Analysis:",
            ["United States (Civilian Unemployment vs. CPI-U)", "India (Urban PLFS Unemployment vs. Combined CPI)"],
            horizontal=True,
            key="pc_country_radio",
        )
    is_us = "United States" in pc_country

    if is_us:
        clean_pc = df_filtered.dropna(subset=["UNRATE", "inflation_yoy"]).copy()
        with col_pc_roll:
            roll_win = st.slider("Rolling Window (Months):", min_value=12, max_value=96, value=48, step=12, key="pc_roll_us")
        fig_pc, slope_val, intercept_val, r2_val, corr_val, n_obs, start_dt, end_dt, eq_str = plot_phillips_curve(
            clean_pc, country="USA", rolling_window=roll_win
        )
        source_name = "Federal Reserve Bank of St. Louis (FRED)"
        series_str = "UNRATE (Civilian Unemployment) vs CPIAUCSL (CPI-U YoY)"
        badge_txt = "LIVE FRED" if is_live_data else "FRED BENCHMARK"
        b_type = "live" if is_live_data else "demo"
        cadence_str = "Monthly Continuous Observations"
    else:
        clean_pc = load_india_quarterly_phillips_dataset()
        with col_pc_roll:
            roll_win = st.slider("Rolling Window (Quarters):", min_value=4, max_value=12, value=8, step=2, key="pc_roll_ind")
        fig_pc, slope_val, intercept_val, r2_val, corr_val, n_obs, start_dt, end_dt, eq_str = plot_phillips_curve(
            clean_pc, country="India", rolling_window=roll_win
        )
        source_name = "MoSPI PLFS & Reserve Bank of India (DBIE)"
        series_str = "Urban Unemployment (PLFS CWS) vs CPI Combined YoY (RBI)"
        badge_txt = "OFFICIAL MOSPI / RBI"
        b_type = "live"
        cadence_str = "Quarterly Observations (2018-Q1 to 2024-Q2)"

    # Formatted Mathematical Regression Equation Banner
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #7E22CE; border-radius:10px; padding:14px 20px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <span style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em;">Estimated Empirical OLS Equation:</span><br>
                <span style="font-size:19px; font-weight:800; color:#0F172A; font-family:'Courier New', monospace;">
                    {eq_str}
                </span>
            </div>
            <div style="display:flex; gap:20px; font-size:12.5px; color:#475569;">
                <div><b>Sample Size (N):</b> {n_obs}</div>
                <div><b>Time Horizon:</b> {pd.to_datetime(start_dt).strftime('%b %Y')} – {pd.to_datetime(end_dt).strftime('%b %Y')}</div>
                <div><b>Sign:</b> <span style="font-weight:700; color:{'#10B981' if slope_val < 0 else '#EF4444'};">{'Inverse Trade-off (β < 0)' if slope_val < 0 else 'Shifting / Non-linear (β ≥ 0)'}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    render_kpi(k1, "Regression Slope (β)", f"{slope_val:+.3f}", "Inflation sensitivity to unemployment", delta_val=slope_val, freq_badge="OLS Slope")
    render_kpi(k2, "Regression Intercept (β₀)", f"{intercept_val:.2f}%", "Baseline implied inflation", freq_badge="OLS Constant")
    render_kpi(k3, "Overall Fit (R²)", f"{r2_val:.3f}", f"Explains {r2_val*100:.1f}% of variation", freq_badge="Goodness of Fit")
    render_kpi(k4, "Pearson Correlation (r)", f"{corr_val:+.3f}", f"Full sample ({n_obs} periods)", freq_badge="Linear Corr")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_c, col_p = st.columns([0.74, 0.26])
    with col_c:
        st.plotly_chart(fig_pc, use_container_width=True)
    with col_p:
        render_data_provenance_card(
            col=col_p,
            title=f"Phillips Curve: {('United States' if is_us else 'India')}",
            source_api=source_name,
            api_key_status="Authentic Official Time Series",
            series_code=series_str,
            frequency=cadence_str,
            currency_unit="Unemployment Rate (%) vs YoY Inflation (%)",
            badge_type=b_type,
            badge_text=badge_txt,
            notes="Analyzes the empirical trade-off between labor market tightness and price inflation across shifting supply and policy regimes."
        )

    # In-Depth Pedagogical & Theoretical Analysis
    tab_theory, tab_shifts, tab_lucas, tab_comparability = st.tabs([
        "1. Theoretical Foundations (Friedman-Phelps)",
        "2. Supply Shocks & Stagflation",
        "3. Lucas Critique & Causality Disclaimer",
        "4. US vs. India Comparability Limitations",
    ])

    with tab_theory:
        st.markdown(
            """
            ### The Classical vs. Expectations-Augmented Phillips Curve

            **1. The Original Phillips Hypothesis (1958):**
            A.W. Phillips originally observed an inverse empirical relationship between the rate of change of nominal wages and civilian unemployment in the United Kingdom (1861–1957). Paul Samuelson and Robert Solow (1960) popularized this as a stable menu of policy options: governments could allegedly choose lower unemployment at the cost of permanently higher inflation.

            **2. The Expectations-Augmented Revolution (Milton Friedman 1968, Edmund Phelps 1967):**
            Friedman and Phelps demonstrated that rational economic agents bargain over **real wages**, not nominal wages. The modern expectations-augmented Phillips Curve is formalized as:

            $$\\pi_t = \\pi_t^e - \\beta (u_t - u_n) + v_t$$

            Where:
            - $\\pi_t$: Actual inflation rate.
            - $\\pi_t^e$: Expected inflation rate.
            - $u_t$: Observed unemployment rate.
            - $u_n$: Natural Rate of Unemployment (NAIRU — Non-Accelerating Inflation Rate of Unemployment).
            - $\\beta$: Slope coefficient measuring labor market sensitivity.
            - $v_t$: Exogenous cost-push supply shock.

            **3. The Long-Run Vertical Phillips Curve:**
            - In the **Short Run**, if actual inflation exceeds expectations ($\\pi_t > \\pi_t^e$), workers misperceive real wage changes, and firms expand hiring, reducing unemployment below $u_n$.
            - In the **Long Run**, expectations adjust fully ($\\pi_t^e = \\pi_t$). Output returns to potential, and unemployment returns to the Natural Rate ($u_t = u_n$). Consequently, the **Long-Run Phillips Curve (LRPC) is vertical**, indicating no permanent trade-off between inflation and unemployment.
            """
        )

    with tab_shifts:
        st.markdown(
            """
            ### Shifting Curves, Supply Shocks & Stagflation

            **Why the Empirical Scatter Plot Often Shows No Simple Downward Slope:**
            In empirical data spanning several decades, the scatter plot frequently resembles an amorphous cloud rather than a clean downward line. This occurs because the short-run Phillips curve **shifts dynamically** over time due to two primary forces:

            **1. Shifts in Inflation Expectations ($\\pi^e$):**
            During the 1970s, as double-digit inflation persisted, public inflation expectations ratcheted upward. Each upward revision in $\\pi^e$ shifted the entire short-run curve upward, so higher inflation occurred at every level of unemployment.

            **2. Adverse Supply Shocks ($v_t > 0$):**
            - **1973 OPEC Oil Embargo & 1979 Iranian Revolution:** Quadrupled energy costs simultaneously reduced aggregate supply (raising unemployment) and accelerated price levels (raising inflation), creating **stagflation**.
            - **2021–2022 Post-Pandemic Supply Chain Bottlenecks:** Container shipping disruptions, semiconductor shortages, and the Russia-Ukraine energy price surge shifted the short-run curve upward globally.
            - Under supply shocks, inflation and unemployment move in the **same direction**, producing positive empirical correlation periods that break the classical negative slope.
            """
        )

    with tab_lucas:
        st.markdown(
            """
            ### The Lucas Critique & Observational Causality Disclaimer

            > **Critical Academic Principle:** *Correlation Does Not Prove Causation.*

            **1. The Lucas Critique (Robert Lucas, 1976):**
            Lucas argued that historical econometric relationships cannot be used to predict the effects of a deliberate policy change. If central bankers attempt to systematically exploit the empirical Phillips Curve by permanently running loose monetary policy to suppress unemployment, forward-looking economic agents anticipate the resulting inflation and adjust their wage and price demands immediately. The historical statistical correlation breaks down precisely when policymakers try to exploit it.

            **2. Non-Causality Disclaimer:**
            The OLS regression line and correlation coefficients displayed above represent **observational descriptive statistics**. They describe the historical joint movement of two endogenous macroeconomic variables; they do **not** imply that low unemployment directly causes inflation, or that central banks can mechanically target unemployment without altering expectations.
            """
        )

    with tab_comparability:
        st.markdown(
            """
            ### Structural Comparability Limitations: India vs. United States

            Direct comparison of the Phillips Curve between the United States and India requires strict academic caution due to fundamental institutional differences:

            | Dimension | United States (FRED) | India (MoSPI & RBI) |
            | :--- | :--- | :--- |
            | **Survey Frequency** | Monthly Continuous (BLS Current Population Survey, N > 400) | Quarterly Urban Bulletins / Annual Rounds (MoSPI PLFS, N = 26) |
            | **Geographic Coverage** | Total Civilian Labor Force (National Urban + Rural) | High-frequency data is Urban only (Current Weekly Status) |
            | **Labor Market Structure** | Predominantly formal contractual wage employment | ~80–85% informal and unorganized employment |
            | **Disguised Unemployment** | Minimal; safety nets allow open job search | High in agriculture; open unemployment understates labor slack |
            | **CPI Food Weight** | ~14% (Food & Beverages) | **45.86%** (All-India Combined CPI basket) |

            **Pedagogical Conclusion:**
            In the US, labor market tightness directly feeds into nominal wage demands and services inflation through formal bargaining channels. In India, headline inflation is predominantly driven by agricultural monsoon conditions, global crude oil prices, and food supply bottlenecks, while informal labor absorbs surplus workers. Consequently, the empirical Phillips relationship in India is structurally weaker and subject to frequent non-linear supply shifts.
            """
        )


# ==============================================================================
# 4. INFLATION FORECAST (RIDGE REGRESSION)
# ==============================================================================
elif selected_page == "Inflation Forecast":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_forecast", on_click=navigate_to, args=(None,))

    st.markdown(
        """
        <div class="content-card">
            <div class="content-card-header">MACHINE LEARNING INFERENCE</div>
            <div class="content-card-title">Predictive Modeling: Next-Quarter Inflation Forecast</div>
            <div class="content-card-sub">Regularized Ridge Regression forecasting next-quarter YoY inflation strictly without lookahead data leakage.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    clean_quarterly, feature_cols, target_col = prepare_quarterly_forecasting_dataset(df_macro)

    if len(clean_quarterly) < 24:
        st.warning(
            f"Insufficient quarterly observations available to calibrate Ridge Regression model: "
            f"{len(clean_quarterly)} quarters found (minimum 24 quarters required for chronological holdout testing)."
        )
    else:
        # Explanatory Methodology Card
        with st.expander("📘 Why Ridge Regression for Macroeconomic Forecasting?", expanded=False):
            st.markdown(
                """
                <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
                    <b>Econometric Motivation:</b> Macroeconomic time series (GDP growth, past inflation, unemployment, interest rates) 
                    exhibit substantial multicollinearity. In standard Ordinary Least Squares (OLS), high correlation among predictors causes 
                    matrix inversion instability and inflates coefficient variance, leading to erratic out-of-sample predictions.<br><br>
                    <b>Ridge Penalty (L2 Regularization):</b> Ridge solves the penalized objective:
                    <div style="background:#F1F5F9; padding:8px; border-radius:4px; font-family:monospace; margin:6px 0;">
                        min_w { (1/N) Σ (y_i − w·x_i)² + α Σ w_j² }
                    </div>
                    By shrinking coefficient weights continuously toward zero (without eliminating them), Ridge controls model variance, guards against 
                    overfitting in small macroeconomic datasets, and yields robust out-of-sample generalization.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Predictor Variable Dictionary Table
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; margin:12px 0 6px 0;'>MACROECONOMIC PREDICTOR FEATURE DICTIONARY</div>", unsafe_allow_html=True)
        feat_rows = []
        for fc in feature_cols:
            m = FEATURE_METADATA.get(fc, {})
            feat_rows.append({
                "Feature Code": fc,
                "Economic Variable": m.get("name", fc),
                "Transmission Role": m.get("role", "Macroeconomic Predictor"),
                "Frequency & Lag": "Quarterly contemporaneous (t)",
                "Economic Rationale": m.get("description", ""),
            })
        st.dataframe(pd.DataFrame(feat_rows), width="stretch")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        ctrl1, ctrl2, ctrl3 = st.columns([0.35, 0.35, 0.3])
        with ctrl1:
            alpha_val = st.slider(
                "Regularization Penalty (α):",
                min_value=0.1,
                max_value=30.0,
                value=2.0,
                step=0.5,
                help="Controls L2 shrinkage penalty. Higher values shrink weights more aggressively toward zero, reducing estimator variance.",
            )
        with ctrl2:
            holdout_pct = st.slider(
                "Chronological Holdout Ratio (%):",
                min_value=10,
                max_value=35,
                value=20,
                step=5,
                help="Strictly out-of-sample holdout test partition. Observations are preserved in chronological order without shuffling.",
            )
        with ctrl3:
            st.markdown(
                """
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:10px 14px; border-radius:10px; font-size:11.5px; color:#475569; margin-top:14px; box-shadow: 0 1px 2px rgba(15,23,42,0.03);">
                    <span style="background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; font-size:10.5px; font-weight:700; padding:2px 6px; border-radius:4px;">RIDGE L₂ PENALTY</span><br>
                    <div style="margin-top:4px;"><b>Target:</b> Next-Quarter YoY Inflation (t+1)<br><b>Validation:</b> Strict Chronological Forward-Split</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        try:
            forecaster = MacroRidgeForecaster(alpha=alpha_val)
            results = forecaster.train_and_evaluate(
                clean_df=clean_quarterly,
                feature_cols=feature_cols,
                target_col=target_col,
                test_ratio=holdout_pct / 100.0,
            )

            # Reliability & Diagnostic Alerts
            if not results.is_reliable or results.reliability_notes:
                for note in results.reliability_notes:
                    st.warning(f"⚠️ **Model Diagnostic Notice:** {note}")

            # 4 Metric Cards with plain-English definitions
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Holdout MAE", f"{results.mae:.2f}%", help="Mean Absolute Error on unseen holdout quarters in percentage points.")
            m2.metric("Holdout RMSE", f"{results.rmse:.2f}%", help="Root Mean Squared Error on unseen holdout quarters (penalizes large forecast errors).")
            m3.metric("Out-of-Sample R²", f"{results.r2:.3f}", help="Proportion of inflation variance explained on unseen holdout data relative to a naive historical mean baseline.")

            if results.next_unseen_forecast is not None:
                lbl = results.next_forecast_label or "Next Quarter"
                m4.metric(f"Next-Quarter Forecast ({lbl})", f"{results.next_unseen_forecast:.2f}%", help=f"Ridge model projection for {lbl}.")
            else:
                m4.metric("Next-Quarter Forecast", "N/A")

            # Actual vs Predicted Plot with Provenance Card
            col_c, col_p = st.columns([0.76, 0.24])
            with col_c:
                fig_pred = plot_actual_vs_predicted(
                    train_df=results.df_train_actual_pred,
                    test_df=results.df_test_actual_pred,
                    split_date=results.split_date,
                    mae=results.mae,
                    rmse=results.rmse,
                    r2=results.r2,
                    next_forecast=results.next_unseen_forecast,
                    next_date=results.next_forecast_date,
                )
                st.plotly_chart(fig_pred, width="stretch")
            with col_p:
                api_status_str = "Trained on FRED Series (FRED_API_KEY in .env)" if is_live_data else "Trained on Offline FRED Benchmark"
                b_type = "sim"
                b_txt = "RIDGE ML"
                render_data_provenance_card(
                    col=col_p,
                    title="Ridge Forecaster (L₂)",
                    source_api="Scikit-Learn Ridge + Federal Reserve Data",
                    api_key_status=api_status_str,
                    series_code="Target: π_t+1 | Features: GDPC1, CPI, UNRATE, FEDFUNDS",
                    frequency="Quarterly Resampled (Lagged t)",
                    currency_unit="Inflation Rate (% YoY)",
                    badge_type=b_type,
                    badge_text=b_txt,
                    notes=f"Chronological split: {results.train_size} train, {results.test_size} test quarters. Penalty α={alpha_val}. No lookahead data leakage."
                )

            # Standardized Ridge Coefficients
            c_bar, c_info = st.columns([0.65, 0.35])
            with c_bar:
                fig_coef = plot_feature_coefficients(results.coefficients)
                st.plotly_chart(fig_coef, width="stretch")

            with c_info:
                train_start_q, train_end_q = results.train_quarter_labels
                test_start_q, test_end_q = results.test_quarter_labels

                st.markdown(
                    f"""
                    <div class="content-card">
                        <div class="content-card-header">CHRONOLOGICAL VALIDATION PROTOCOL</div>
                        <div style="font-size: 12px; color: #334155; line-height: 1.6;">
                            <b>Target Variable:</b> YoY Inflation at quarter t+1 (π<sub>t+1</sub>)<br>
                            <b>Predictors Observed at t:</b> Real GDP Growth, Inflation, Unemployment, Fed Funds Rate<br>
                            <b>Training Window:</b> {train_start_q} – {train_end_q} ({results.train_size} quarters)<br>
                            <b>Holdout Test Window:</b> {test_start_q} – {test_end_q} ({results.test_size} quarters)<br>
                            <b>Standardization:</b> StandardScaler fitted strictly on training partition only.<br>
                            <b>Data Leakage Prevention:</b> Strictly chronological; future observations never enter training feature matrix.<br>
                            <b>Forecast Nature:</b> Conditional statistical projection, not an infallible or guaranteed forecast.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Latest Input Features Table used for next-quarter prediction
            if results.latest_feature_values:
                with st.expander(f"🔍 Latest Predictor Values Used for {results.next_forecast_label} Projection"):
                    st.markdown("These are the most recent empirical observations fed into the calibrated Ridge model:")
                    input_records = []
                    for k, val in results.latest_feature_values.items():
                        meta = FEATURE_METADATA.get(k, {})
                        input_records.append({
                            "Predictor Variable": meta.get("name", k),
                            "Observed Value": f"{val:.2f}%",
                            "Economic Role": meta.get("role", ""),
                        })
                    st.dataframe(pd.DataFrame(input_records), width="stretch")

        except Exception as exc:
            st.error(f"Ridge Model Training Exception: {exc}")


# ==============================================================================
# 4. INDIA MULTI-INDICATOR MACROECONOMIC FORECASTING
# ==============================================================================
elif selected_page == "India Macro Forecast":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_india_forecast", on_click=navigate_to, args=(None,))

    # Hero Banner
    st.markdown(
        """
        <div style="background:linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 50%, #F5F3FF 100%); border:1px solid #DDD6FE; border-radius:16px; padding:22px 26px; margin-bottom:20px; box-shadow:0 4px 18px rgba(124,58,237,0.04);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#0F172A; letter-spacing:-0.03em; margin-bottom:4px;">India Multi-Indicator Macroeconomic Forecasting</div>
                    <div style="font-size:13.5px; color:#475569; max-width:880px; line-height:1.55;">
                        Official empirical time-series forecasting across <b>CPI Inflation</b>, <b>Real GDP Growth</b>, and <b>Industrial Production (IIP)</b> using linear regularized <b>Ridge Regression</b> with strict zero-lookahead chronological validation. Evaluated against authentic central bank persistence benchmarks (y<sub>t+1</sub> = y<sub>t</sub>).
                    </div>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <span class="badge-live-pill"><span class="pulse-dot-live"></span> RBI DBIE & MoSPI</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load Indian Forecasting Datasets
    try:
        india_datasets = load_india_forecasting_data()
        prov_info = india_datasets.get("provenance_info", {})
    except Exception as exc:
        st.error(f"Error loading Indian macroeconomic data: {exc}")
        st.stop()

    # Target Switcher Controls
    col_t1, col_t2 = st.columns([0.62, 0.38])
    with col_t1:
        target_keys = ["target_a_cpi", "target_b_gdp", "target_c_iip"]
        target_labels = {
            "target_a_cpi": "Target A: Next-Quarter CPI Inflation (% YoY)",
            "target_b_gdp": "Target B: Next-Quarter Real GDP Growth (% YoY)",
            "target_c_iip": "Target C: Next-Month IIP Industrial Growth (% YoY)",
        }
        selected_target_key = st.segmented_control(
            "Select Forecasting Target",
            options=target_keys,
            format_func=lambda k: target_labels[k],
            default="target_a_cpi",
            key="india_target_pill",
        )
        if selected_target_key is None:
            selected_target_key = "target_a_cpi"

    with col_t2:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:10px 16px; font-size:12px; color:#475569; line-height:1.45;">
                <b style="color:#0F172A;">Strict Methodology Guarantee:</b> No future information leakage. Scaler fit solely on training partition. Each target calibrated independently using authentic empirical series.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Interactive Model Hyperparameters Container
    with st.container():
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px 20px; margin-bottom:16px; box-shadow:0 1px 3px rgba(15,23,42,0.03);">
                <div style="font-size:12px; font-weight:700; color:#6D28D9; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">
                    ⚙️ Ridge Regularization & Chronological Split Calibration
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c_alpha, c_split = st.columns(2)
        with c_alpha:
            alpha_val = st.slider(
                "L2 Penalty / Shrinkage Strength (α)",
                min_value=0.01,
                max_value=50.0,
                value=1.0,
                step=0.1,
                help="Controls parameter shrinkage in Ridge Regression: min ||y - Xw||² + α||w||². Resolves macro multicollinearity without omitting predictors.",
                key="india_alpha_slider",
            )
        with c_split:
            holdout_val = st.slider(
                "Out-of-Sample Chronological Holdout Partition",
                min_value=0.15,
                max_value=0.35,
                value=0.20,
                step=0.05,
                format="%d%%",
                help="Strict chronological holdout (arrow of time). No future shuffle leakage.",
                key="india_holdout_slider",
            )

    # Calibrate Model for Selected Target
    target_dict = india_datasets[selected_target_key]
    forecaster = IndiaMultiForecaster(alpha=alpha_val)
    eval_res = forecaster.evaluate_target(target_dict, selected_target_key, test_ratio=holdout_val)

    # KPI Summary Row: 5 elevated cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    render_kpi(
        kpi1,
        title="Next Ridge Forecast",
        value_str=f"{eval_res.next_period_ridge_forecast:.2f}{eval_res.target_unit}",
        sub_str=f"Target: {eval_res.target_period_label}",
        delta_val=eval_res.next_period_ridge_forecast - eval_res.current_value_at_origin,
        delta_suffix=eval_res.target_unit,
        delta_label=f"vs Current ({eval_res.forecast_origin_label})",
        freq_badge=eval_res.frequency,
    )
    render_kpi(
        kpi2,
        title="Forecast Origin",
        value_str=eval_res.forecast_origin_label,
        sub_str=f"Latest Obs: {eval_res.forecast_origin_date.strftime('%b %Y')}",
        delta_val=eval_res.current_value_at_origin,
        delta_suffix=eval_res.target_unit,
        delta_label="Observed Level",
        freq_badge=eval_res.frequency,
    )
    render_kpi(
        kpi3,
        title="Holdout Test MAE",
        value_str=f"{eval_res.ridge_mae:.2f}%",
        sub_str=f"Persistence: {eval_res.persistence_mae:.2f}%",
        delta_val=eval_res.persistence_mae - eval_res.ridge_mae,
        delta_suffix="% pts",
        invert_color=False,
        delta_label="Ridge Advantage" if eval_res.ridge_mae <= eval_res.persistence_mae else "Persist Advantage",
        freq_badge="Out of Sample",
    )
    render_kpi(
        kpi4,
        title="Holdout Test RMSE",
        value_str=f"{eval_res.ridge_rmse:.2f}%",
        sub_str=f"Persistence: {eval_res.persistence_rmse:.2f}%",
        delta_val=eval_res.persistence_rmse - eval_res.ridge_rmse,
        delta_suffix="% pts",
        delta_label="Ridge Advantage" if eval_res.ridge_rmse <= eval_res.persistence_rmse else "Persist Advantage",
        freq_badge="Out of Sample",
    )
    render_kpi(
        kpi5,
        title="Holdout Test R²",
        value_str=f"{eval_res.ridge_r2:.3f}",
        sub_str=f"Train N={eval_res.train_size} | Test N={eval_res.test_size}",
        delta_val=eval_res.ridge_r2 - eval_res.persistence_r2,
        delta_suffix="",
        delta_label="vs Persistence R²",
        freq_badge="Out of Sample",
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Side-by-Side Chart and Institutional Provenance Card
    chart_col, prov_col = st.columns([0.72, 0.28])

    with chart_col:
        st.plotly_chart(
            plot_india_target_forecast(eval_res),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with prov_col:
        # Determine source series metadata
        if selected_target_key == "target_a_cpi":
            p_title = "All-India CPI Combined Index"
            p_source = "RBI DBIE & MoSPI eSankhyiki"
            p_table = "real_sector.cpi_ruc_rn / C_GIAG"
            p_freq = "Monthly (Aggregated to Quarterly)"
            p_unit = "% YoY (Base 2012 = 100)"
            p_notes = (
                "Monthly CPI averaged across 3 months per quarter to harmonize with Real GDP. "
                "Target is quarter q+1 inflation using predictors observable at quarter q."
            )
            p_live = prov_info.get("cpi", {}).get("live", True)
        elif selected_target_key == "target_b_gdp":
            p_title = "Quarterly Real GDP (2011-12 Prices)"
            p_source = "RBI DBIE Official API Mirror"
            p_table = "real_sector.qtr_gdp_mrkt_prc_rn / CEXP_GDP_MARK_CST"
            p_freq = "Quarterly (National Accounts)"
            p_unit = "% YoY Real Growth (₹ Crores)"
            p_notes = (
                "Computed as 4-quarter percentage change in constant price GDP. "
                "Lagged IIP, CPI, and policy rates aligned chronologically."
            )
            p_live = prov_info.get("gdp", {}).get("live", True)
        else:
            p_title = "Index of Industrial Production (IIP)"
            p_source = "RBI DBIE & MoSPI eSankhyiki"
            p_table = "real_sector.inx_inds_prod_rn / SEC_GEN_INDX"
            p_freq = "Monthly (Native Observation Frequency)"
            p_unit = "% YoY Growth (Base 2011-12 = 100)"
            p_notes = (
                "Modeled at its native monthly frequency without artificial quarterly compression. "
                "Target is month m+1 growth using origin month m features."
            )
            p_live = prov_info.get("iip", {}).get("live", True)

        render_data_provenance_card(
            col=prov_col,
            title=p_title,
            source_api=p_source,
            api_key_status="Open Access DBIE API Mirror (Public Access)",
            series_code=p_table,
            frequency=p_freq,
            currency_unit=p_unit,
            badge_type="live" if p_live else "demo",
            badge_text="LIVE RBI FEED" if p_live else "RBI BENCHMARK",
            notes=p_notes,
        )

    # Comparative Model Diagnostics & Transmission Channels Section
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Diagnostic Verdict Banner
    verdict_border = "#BBF7D0" if eval_res.ridge_beats_persistence else "#FDE68A"
    verdict_bg = "#F0FDF4" if eval_res.ridge_beats_persistence else "#FFFBEB"
    verdict_color = "#166534" if eval_res.ridge_beats_persistence else "#92400E"
    verdict_tag = "RIDGE REGRESSION OUTPERFORMS PERSISTENCE" if eval_res.ridge_beats_persistence else "PERSISTENCE BENCHMARK HOLDS THE EDGE"

    st.markdown(
        f"""
        <div style="background:{verdict_bg}; border:1.5px solid {verdict_border}; border-radius:14px; padding:16px 20px; margin-bottom:18px;">
            <div style="font-size:11px; font-weight:800; color:{verdict_color}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">
                EVALUATION DIAGNOSTIC VERDICT: {verdict_tag}
            </div>
            <div style="font-size:13.5px; color:#1E293B; line-height:1.55;">
                {eval_res.verdict_summary}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Two diagnostic visualization charts
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.plotly_chart(
            plot_india_model_comparison(eval_res),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with d_col2:
        st.plotly_chart(
            plot_india_coefficients(eval_res),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # Feature Transmission Mechanism Table
    st.markdown(
        """
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:18px 22px; margin-bottom:18px; box-shadow:0 1px 3px rgba(15,23,42,0.03);">
            <div style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:4px;">Predictor Dictionary & Macroeconomic Transmission Channels</div>
            <div style="font-size:12.5px; color:#64748B; margin-bottom:14px;">
                Standardized coefficients indicate the directional push of each economic variable on the target period, scaled by feature standard deviation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display clean table
    coef_display_df = eval_res.coefficients[[
        "Feature_Name",
        "Standardized_Coefficient",
        "Impact_Direction",
        "Economic_Role",
        "Channel",
    ]].copy()
    coef_display_df.columns = [
        "Predictor Variable",
        "Standardized Weight (β)",
        "Transmission Direction",
        "Economic Role",
        "Economic Transmission Channel",
    ]
    st.dataframe(coef_display_df, width="stretch", hide_index=True)

    # Expandable Raw Data Inspector
    with st.expander(f"🔍 Inspect Harmonized Training & Evaluation Dataset ({eval_res.total_samples} observations)"):
        st.markdown(
            "Below is the underlying aligned time-series dataset with strictly contemporaneous features at origin t and forward target at t+1:"
        )
        st.dataframe(target_dict["df"], width="stretch")


# ==============================================================================
# 5. POLICY LAB
# ==============================================================================
elif selected_page == "Policy Lab":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_policy", on_click=navigate_to, args=(None,))

    st.markdown(
        """
        <div class="content-card">
            <div class="content-card-header">POLICY SANDBOX & COMPARATIVE STATICS</div>
            <div class="content-card-title">Macroeconomic Policy Simulation Lab</div>
            <div class="content-card-sub">Interactive counterfactual policy sandbox: Keynesian Expenditure Multiplier and Simplified IS–LM Equilibrium.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_policy_a, tab_policy_b = st.tabs([
        "Policy Simulator A: Government Spending (Keynesian Multiplier)",
        "Policy Simulator B: Interest-Rate Shock (IS–LM Framework)",
    ])

    # --------------------------------------------------------------------------
    # SIMULATOR A: KEYNESIAN MULTIPLIER
    # --------------------------------------------------------------------------
    with tab_policy_a:
        st.markdown(
            """
            <div style="background:#FFF7ED; border:1px solid #FFEDD5; padding:14px 18px; border-radius:12px; margin-bottom:16px;">
                <span style="background:#FFF7ED; color:#EA580C; border:1px solid #FDBA74; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">CLASSICAL KEYNESIAN EXPENDITURE ENGINE</span><br>
                <div style="margin-top:6px; font-weight:700; color:#0F172A; font-size:13.5px;">Keynesian Multiplier Formulation:</div>
                <code style="font-size:13px; color:#C2410C;">ΔY = ΔG / (1 − MPC) = k · ΔG</code>, where <code>k = 1 / MPS</code>.<br>
                <div style="font-size:12px; color:#475569; line-height:1.55; margin-top:6px;">
                    <b>Documented Model Parameters:</b> Marginal Propensity to Consume (MPC) is fixed at the standard empirical benchmark of 
                    <b>0.75</b> (Marginal Propensity to Save MPS = 0.25, expenditure multiplier k = 4.00). 
                    Adjust autonomous government spending (ΔG) below to evaluate illustrative cumulative output expansion.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # EXACTLY ONE SLIDER FOR SIMULATOR A
        delta_g_val = st.slider(
            "Autonomous Government Spending Policy Shock ΔG (₹ Billions):",
            min_value=-40000.0,
            max_value=80000.0,
            value=8000.0,
            step=2000.0,
            help="Simulates an expansionary (positive) or contractionary (negative) autonomous spending shift in Indian Rupees (₹B).",
        )

        sim_keynes = simulate_keynesian_multiplier(delta_g=delta_g_val, mpc=0.75)

        ka1, ka2, ka3, ka4 = st.columns(4)
        ka1.metric("Government Injection (ΔG)", f"₹{sim_keynes.delta_g:+,.1f}B", help="Autonomous fiscal expenditure shock in Indian Rupees.")
        ka2.metric("Expenditure Multiplier (k)", f"{sim_keynes.multiplier:.2f}x", help="Formula: k = 1 / (1 − MPC).")
        ka3.metric("Total Output Impact (ΔY)", f"₹{sim_keynes.delta_y:+,.1f}B", help="Formula: ΔY = k × ΔG.")
        ka4.metric("MPS Assumption", f"{sim_keynes.mps:.2f}", help="Marginal Propensity to Save (1 − MPC).")

        col_c, col_p = st.columns([0.76, 0.24])
        with col_c:
            fig_keynes = plot_keynesian_rounds(sim_keynes.rounds_breakdown)
            st.plotly_chart(fig_keynes, width="stretch")
        with col_p:
            render_data_provenance_card(
                col=col_p,
                title="Keynesian Multiplier Engine",
                source_api="Macroeconomic Theoretical Simulation",
                api_key_status="No API Key Required (Closed Analytical Solution)",
                series_code="ΔY = k · ΔG = ΔG / (1 - MPC)",
                frequency="Comparative Statics Equilibrium",
                currency_unit="Indian Rupees (₹ Billions)",
                badge_type="sim",
                badge_text="THEORETICAL",
                notes=f"Autonomous shock ΔG = ₹{sim_keynes.delta_g:+,.1f}B. MPC benchmark = {sim_keynes.mpc:.2f}, MPS = {sim_keynes.mps:.2f}, multiplier k = {sim_keynes.multiplier:.2f}."
            )

        with st.expander("View Sequential Expenditure Rounds Table", expanded=True):
            st.dataframe(sim_keynes.rounds_breakdown, width="stretch")

        st.markdown(
            f"""
            <div class="content-card">
                <div class="content-card-header">THEORETICAL TRANSMISSION & PEDAGOGICAL ASSUMPTIONS</div>
                <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
                    {sim_keynes.explanation}<br><br>
                    <b>Underlying Assumptions & Theoretical Boundaries:</b>
                    <ul style="margin: 4px 0 0 16px; padding: 0;">
                        <li><b>Excess Capacity:</b> Assumes the macroeconomy operates below full employment with spare resources to meet higher demand without triggering price inflation.</li>
                        <li><b>Fixed Price Level:</b> In this simple model, the price level P is fixed; in reality, aggregate demand expansion along an upward-sloping AS curve partially dissipates into price inflation.</li>
                        <li><b>Zero Financial Crowding Out:</b> Assumes the central bank holds interest rates constant; if interest rates rise in response to higher GDP, investment crowding-out would reduce the effective multiplier.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------------------------
    # SIMULATOR B: IS-LM INTEREST RATE SHOCK
    # --------------------------------------------------------------------------
    with tab_policy_b:
        st.markdown(
            """
            <div style="background:#FFF7ED; border:1px solid #FFEDD5; padding:14px 18px; border-radius:12px; margin-bottom:16px;">
                <span style="background:#FFF7ED; color:#EA580C; border:1px solid #FDBA74; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">SIMPLIFIED IS–LM EQUILIBRIUM FRAMEWORK</span><br>
                <div style="margin-top:6px; font-weight:700; color:#0F172A; font-size:13.5px;">Macroeconomic Goods & Money Market Transmission:</div>
                <div style="font-size:12px; color:#475569; line-height:1.55; margin-top:6px;">
                    • <b>Goods Market (IS Curve):</b> <code>Y = [A − b · r] / (1 − c)</code>, where autonomous expenditure <code>A = ₹600B</code>, MPC <code>c = 0.75</code>, investment sensitivity <code>b = 50.0</code>.<br>
                    • <b>Money Market (LM Curve):</b> <code>(M/P) = k_y · Y − h · r</code>, where money demand sensitivity <code>k_y = 0.20</code>, speculative sensitivity <code>h = 40.0</code>, price level <code>P = 1.0</code>.<br>
                    • <b>Transmission Channel:</b> The central bank alters the policy interest rate. Rate hikes (+Δr) raise the cost of capital, depressing investment along the IS curve and contracting equilibrium output; the money supply adjusts endogenously to sustain the policy rate.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # EXACTLY ONE SLIDER FOR SIMULATOR B (EXACTLY TWO SLIDERS ACROSS THE APPLICATION)
        delta_r_val = st.slider(
            "Central Bank Policy Interest Rate Shock Δr (Percentage Points):",
            min_value=-3.0,
            max_value=3.0,
            value=0.5,
            step=0.25,
            help="Simulates central bank monetary policy tightening (+Δr) or easing (−Δr).",
        )

        sim_islm = simulate_is_lm(delta_g=0.0, delta_r=delta_r_val)

        kb1, kb2, kb3, kb4 = st.columns(4)
        kb1.metric("Equilibrium Output Y*", f"₹{sim_islm.y_new:,.1f}B", delta=f"{sim_islm.delta_y:+,.1f}B Output Shift")
        kb2.metric("Equilibrium Interest Rate r*", f"{sim_islm.r_new:.2f}%", delta=f"{sim_islm.delta_r:+.2f}% Rate Shock")
        kb3.metric("Baseline Output Y₀*", f"₹{sim_islm.y_base:,.1f}B")
        kb4.metric("Baseline Rate r₀*", f"{sim_islm.r_base:.2f}%")

        col_c, col_p = st.columns([0.76, 0.24])
        with col_c:
            fig_islm = plot_is_lm_curves(
                curve_df=sim_islm.curve_df,
                y_base=sim_islm.y_base,
                r_base=sim_islm.r_base,
                y_new=sim_islm.y_new,
                r_new=sim_islm.r_new,
            )
            st.plotly_chart(fig_islm, width="stretch")
        with col_p:
            render_data_provenance_card(
                col=col_p,
                title="IS–LM Equilibrium Simulator",
                source_api="Macroeconomic Theoretical Simulation",
                api_key_status="No API Key Required (Analytical Equilibrium)",
                series_code="IS: Y = (A - br)/(1-c) | LM: M/P = ky·Y - hr",
                frequency="Comparative Statics Equilibrium",
                currency_unit="Output Y* in ₹ Billions, Interest Rate r* in %",
                badge_type="sim",
                badge_text="THEORETICAL",
                notes=f"Monetary policy rate shock Δr = {delta_r_val:+.2f} percentage points. Money market liquidity endogenously clears at policy rate."
            )

        # Step-by-Step Transmission Mechanism Card
        st.markdown(
            f"""
            <div class="content-card">
                <div class="content-card-header">STEP-BY-STEP ECONOMIC TRANSMISSION MECHANISM</div>
                <div style="font-size: 12.5px; color: #334155; line-height: 1.6;">
                    {"<br>".join(sim_islm.transmission_steps)}
                    <br><br>
                    <b>Documented Parameter Assumptions:</b><br>
                    MPC <i>c = 0.75</i>, Investment Sensitivity <i>b = 50.0</i>, Money Demand <i>k_y = 0.20</i>, Speculative Sensitivity <i>h = 40.0</i>, Price Level <i>P = 1.0</i>, Autonomous Spending <i>A₀ = ₹600B</i>, Baseline Money Supply <i>M₀ = ₹600B</i>.<br><br>
                    <i>Methodological Limitations: This is a stylized closed-economy comparative statics model designed for educational demonstration. It abstracts from exchange-rate dynamics, inflationary feedback, and term premia. Outputs are illustrative scenarios, not commercial forecasts.</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# 6. DATA SOURCES & METHODOLOGY
# ==============================================================================
elif selected_page == "Data Sources":
    col_back, _ = st.columns([0.22, 0.78])
    with col_back:
        st.button("← Return to Homepage", key="back_from_datasources", on_click=navigate_to, args=(None,))

    st.markdown(
        """
        <div class="content-card">
            <div class="content-card-header">TRANSPARENCY & BOUNDARIES</div>
            <div class="content-card-title">Data Sources, Inventory & Institutional Methodology</div>
            <div class="content-card-sub">Comprehensive series metadata, international cross-country explorer, and econometric boundaries.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_india, tab_inv, tab_wb, tab_rules = st.tabs([
        "Indian Official Series (RBI DBIE & MoSPI)",
        "FRED Series Inventory (US)",
        "World Bank API V2 (Cross-Country)",
        "Methodological Boundaries & Limitations",
    ])

    with tab_india:
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:8px;'>RESERVE BANK OF INDIA (DBIE) & MOSPI NATIONAL MACROECONOMIC SERIES</div>", unsafe_allow_html=True)
        india_inv_records = []
        for key, meta in INDIAN_MACRO_SERIES.items():
            india_inv_records.append({
                "Indicator Key": key,
                "Concept & Series Name": meta["name"],
                "Official Source": meta["source"],
                "API Schema / Table": meta["table"],
                "Series Code": meta["code"],
                "Observation Cadence": meta["frequency"],
                "Units / Base": meta["units"],
                "Description": meta["description"],
            })
        st.dataframe(pd.DataFrame(india_inv_records), width="stretch", hide_index=True)

        st.markdown("<div style='font-size:11px; font-weight:700; color:#15803D; text-transform:uppercase; margin-top:16px; margin-bottom:8px;'>INDIAN STATE-LEVEL ECONOMIC & LABOUR INVENTORY (RBI DBIE & MOSPI PLFS)</div>", unsafe_allow_html=True)
        state_inv_records = []
        for key, meta in INDIAN_STATE_SERIES.items():
            state_inv_records.append({
                "Series Key": key,
                "Official Concept": meta["name"],
                "Data Source": meta["source"],
                "Table Reference": meta["table"],
                "Cadence": meta["frequency"],
                "Units": meta["units"],
                "Geographic Scope": meta.get("coverage", "All States & UTs"),
            })
        st.dataframe(pd.DataFrame(state_inv_records), width="stretch", hide_index=True)

        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px; margin-top:14px; font-size:12.5px; color:#334155; line-height:1.6;">
                <b style="color:#0F172A;">API Integration & Access Modes:</b><br>
                • <b>RBI DBIE Open API Mirror:</b> Queried keyless via <code>https://data-api.dbie.rbihub.in</code>. Covers All-India CPI Combined Base 2012 (<code>cpi_ruc_rn</code>), State CPI Combined (<code>cpi_ruc_st_rn</code>), Quarterly Real GDP (<code>qtr_gdp_mrkt_prc_rn</code>), IIP (<code>inx_inds_prod_rn</code>), WACR (<code>war_call_money_rn</code>), State Domestic Product (Tables 65/66), Per Capita Income (Tables 227/250), and State Finances (<code>st_fin_std_budgets_rn</code>).<br>
                • <b>MoSPI Periodic Labour Force Survey (PLFS):</b> State-level LFPR, WPR, and Unemployment Rate (UR) sourced directly from official NSSO Annual Survey Reports (Table 1, 2, and 4) in Usual Status (ps+ss) for persons of age 15 years and above.<br>
                • <b>MoSPI eSankhyiki API:</b> Official endpoints at <code>https://api.mospi.gov.in</code>. Public preview access operates without credentials; authenticated production access is enabled by setting <code>MOSPI_API_TOKEN</code> in your local <code>.env</code> file.<br>
                • <b>Legacy SSL Handshake Adapter:</b> Python transport uses an internal <code>LegacySSLAdapter</code> (enabling <code>OP_LEGACY_SERVER_CONNECT</code>) to resolve OpenSSL handshake negotiation on Indian national servers without third-party proxy dependencies.<br>
                • <b>Empirical Verification:</b> All fallbacks and benchmarks use genuine historical series extracted directly from RBI and MoSPI statistical bulletins. Zero synthetic data fabrication.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_inv:
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:8px;'>FRED API APPROVED TIME-SERIES INVENTORY</div>", unsafe_allow_html=True)
        inventory_records = []
        for key, meta in FRED_SERIES.items():
            inventory_records.append({
                "Series Code": meta["id"],
                "Economic Concept": meta["name"],
                "Observation Cadence": meta["frequency"],
                "Reporting Units": meta["units"],
                "Description": meta["description"],
            })
        st.dataframe(pd.DataFrame(inventory_records), width="stretch")

        status_text = "🟢 Live authenticated queries to Federal Reserve Bank of St. Louis API active." if is_live_data else "🟡 Demonstration snapshot active. Historical US benchmark data loaded safely (no fake data created)."
        st.info(status_text)

    with tab_wb:
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:8px;'>WORLD BANK INDICATORS API V2 EXPLORER</div>", unsafe_allow_html=True)
        st.markdown(
            "Annual cross-country macroeconomic series queried directly from World Bank Open Data (unauthenticated). "
            "Data is reported on an **annual historical basis** (latest reporting year typically t-1 or t-2) and does not represent real-time high-frequency data."
        )

        col_c, col_i = st.columns(2)
        with col_c:
            sel_country = st.selectbox(
                "Select Country:",
                options=list(SUPPORTED_COUNTRIES.keys()),
                format_func=lambda x: f"{x} — {SUPPORTED_COUNTRIES[x]}",
                index=0,
            )
        with col_i:
            sel_wb_ind = st.selectbox(
                "Select Approved Indicator:",
                options=list(WORLD_BANK_INDICATORS.keys()),
                format_func=lambda x: f"{WORLD_BANK_INDICATORS[x]['name']} ({WORLD_BANK_INDICATORS[x]['code']})",
                index=0,
            )

        with st.spinner("Fetching World Bank data..."):
            wb_client = WorldBankClient()
            df_wb, wb_live, wb_err = wb_client.fetch_indicator(
                country_code=sel_country,
                indicator_code=WORLD_BANK_INDICATORS[sel_wb_ind]["code"],
                start_year=1995,
                end_year=2023,
            )

        if wb_err:
            st.warning(wb_err)
        elif not df_wb.empty:
            col_c, col_p = st.columns([0.76, 0.24])
            with col_c:
                fig_wb = plot_world_bank_indicator(
                    df_wb,
                    country_name=SUPPORTED_COUNTRIES[sel_country],
                    indicator_name=WORLD_BANK_INDICATORS[sel_wb_ind]["name"],
                )
                st.plotly_chart(fig_wb, width="stretch")
            with col_p:
                render_data_provenance_card(
                    col=col_p,
                    title="World Bank Open Data",
                    source_api="World Bank Indicators API V2",
                    api_key_status="Keyless Open Access (api.worldbank.org/v2)",
                    series_code=WORLD_BANK_INDICATORS[sel_wb_ind]["code"],
                    frequency="Annual Historical Series (1995–2023)",
                    currency_unit=f"Indicator: {WORLD_BANK_INDICATORS[sel_wb_ind]['name']}",
                    badge_type="wb",
                    badge_text="LIVE WORLD BANK",
                    notes=f"Country: {SUPPORTED_COUNTRIES[sel_country]} ({sel_country}). Official global repository."
                )

            with st.expander("View Annual Indicator Data Table"):
                st.dataframe(
                    df_wb[["year", "value", "country", "indicator"]].sort_values("year", ascending=False),
                    width="stretch",
                )
        else:
            st.info("No data returned for selected country and indicator.")

    with tab_rules:
        st.markdown(
            f"""
            <div class="content-card">
                <div class="content-card-header">1. DATA HARMONIZATION & FREQUENCY RULES</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Monthly Baseline Alignment:</b> CPI-U, Civilian Unemployment, Federal Funds Rate, and 10Y Treasury yields are aligned monthly.<br>
                    • <b>Quarterly GDP Alignment:</b> Real GDP is published quarterly. On monthly views, the latest known quarterly GDP figure is forward-filled only within its 3-month release window (limit=2) without lookahead interpolation or fabricating future quarters.<br>
                    • <b>Quarterly ML Alignment:</b> For Ridge forecasting, monthly series are averaged quarterly to naturally align with Real GDP releases, preventing frequency distortion.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">2. MACHINE LEARNING SAFEGUARDS (RIDGE ONLY)</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Zero Lookahead Leakage:</b> To predict next-quarter inflation (t+1), all features are strictly observed at or before quarter t.<br>
                    • <b>Chronological Validation:</b> Training and holdout splits preserve strict chronological ordering. Random permutations or shuffling are strictly prohibited.<br>
                    • <b>Feature Standardization:</b> StandardScaler is fitted solely on the training partition and applied to holdout samples.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">3. POLICY SIMULATORS VS. EMPIRICAL FORECASTS</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Keynesian Multiplier:</b> Pedagogical calculation assuming constant prices and excess capacity. Illustrative of round-by-round induced consumption.<br>
                    • <b>IS–LM Framework:</b> Stylized comparative statics under a closed economy and fixed short-run price level. Designed for academic demonstration, not guaranteed market forecasts.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">4. BUSINESS-CYCLE REGIMES & NBER RECESSION CHRONOLOGY</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>US Authoritative Source:</b> Official recession peaks and troughs are established by the <i>National Bureau of Economic Research (NBER) Business Cycle Dating Committee</i>. A recession involves a significant decline in economic activity spread across the economy lasting more than a few months, visible in nonfarm payroll employment, real personal income less transfers, real personal consumption expenditures, wholesale-retail sales, and real GDP.<br>
                    • <b>India Analytical Slowdown Rule:</b> India has no official recession-dating committee equivalent to NBER. To avoid misleading classifications, an <i>analytical growth slowdown regime</i> is defined transparently as ≥ 2 consecutive quarters where Real GDP YoY growth is below 5.0% (below potential trend) or negative (contraction). Labeled strictly as analytical slowdowns, not official recessions.<br>
                    • <b>Non-Causality Boundary:</b> Indicator statistics across regimes represent historical descriptive associations, not causal effects.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">5. CLASSICAL MATHEMATICAL TIME SERIES DECOMPOSITION</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Additive Formulation:</b> Y_t = Trend_t + Seasonal_t + Residual_t.<br>
                    • <b>Trend Estimation:</b> 2×12 centered moving average filter applied to monthly CPI series to eliminate annual seasonality.<br>
                    • <b>Normalized Seasonal Component:</b> Calculated from detrended monthly deviations and normalized so the 12 calendar monthly factors sum to zero (Σ S_m = 0).<br>
                    • <b>Residual Component:</b> Computed directly as Residual_t = Y_t − Trend_t − Seasonal_t, capturing irregular variations and exogenous supply shocks.<br>
                    • <b>Frequency Verification:</b> Monthly continuity is mathematically verified prior to decomposition. Gaps are reported transparently without unverified synthetic interpolation.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">6. WORLD BANK MULTI-COUNTRY COMPARABILITY METHODOLOGY</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Approved Indicators:</b> Real GDP Growth (<code>NY.GDP.MKTP.KD.ZG</code>), CPI Inflation (<code>FP.CPI.TOTL.ZG</code>), and Unemployment Rate (<code>SL.UEM.TOTL.ZS</code>).<br>
                    • <b>Common-Year Alignment:</b> Cross-country league tables and rankings evaluate shared calendar years where all selected economies have verified observations, preventing sample selection bias.<br>
                    • <b>No Single Composite Score:</b> Indicators are analyzed independently to preserve the distinct structural relationships between growth, price stability, and labor markets.<br>
                    • <b>Keyless Public Access:</b> Operates directly against World Bank Indicators API V2 endpoints with resilient offline benchmark backups.
                </div>
            </div>

            <div class="content-card">
                <div class="content-card-header">7. PHILLIPS CURVE ECONOMETRIC FOUNDATIONS & LUCAS CRITIQUE</div>
                <div style="font-size:12.5px; color:#334155; line-height:1.6;">
                    • <b>Observational OLS Fit:</b> The linear regression π̂ = β₀ + β₁·u describes observed statistical correlation over a specified sample period.<br>
                    • <b>Expectations-Augmentation:</b> In accordance with Friedman (1968) and Phelps (1967), the short-run curve shifts dynamically with inflation expectations (π_t = π_t^e − β(u_t − u_n) + v_t). In the long run, expectations adjust, rendering the long-run curve vertical at NAIRU.<br>
                    • <b>Lucas Critique Disclaimer:</b> Historical statistical correlations cannot be treated as an exploitable policy menu. Attempting to artificially manipulate unemployment by inducing inflation alters public expectations, causing the empirical relationship to break down.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
