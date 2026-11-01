"""EcoSim FastAPI Backend Application.

Provides macroeconomic data APIs, Ridge forecasting, Keynesian multiplier,
and IS-LM simulation endpoints for the EcoSim platform.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import (
    FRED_API_KEY,
    FRED_SERIES,
    WORLD_BANK_INDICATORS,
    SUPPORTED_COUNTRIES,
)
from backend.data_service import data_service
from backend.models_service import models_service
from backend.simulation_service import simulation_service
from backend.cache import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecosim.api")

app = FastAPI(
    title="EcoSim: Global Macroeconomic Intelligence API",
    version="2.0.0",
    description="Real-Time Economic Data Analytics, Ridge Regression Forecasting & Policy Simulation Dashboard",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Schemas
class RidgeForecastRequest(BaseModel):
    country_code: str = Field(default="USA", description="3-letter ISO country code")
    alpha: float = Field(default=1.0, ge=0.001, le=100.0, description="Regularization penalty (lambda)")
    test_ratio: float = Field(default=0.20, ge=0.10, le=0.40, description="Chronological holdout ratio")
    features: list[str] = Field(
        default=["inflation_lag", "unemployment", "gdp_growth", "interest_rate"],
        description="Feature names to include",
    )


class KeynesianSimRequest(BaseModel):
    baseline_gdp: float = Field(default=27800.0, ge=1.0, description="Baseline national income ($B)")
    delta_g: float = Field(default=250.0, description="Autonomous government spending change ($B)")
    mpc: float = Field(default=0.75, ge=0.01, lt=1.0, description="Marginal Propensity to Consume")
    tax_rate: float = Field(default=0.0, ge=0.0, le=0.50, description="Proportional income tax rate")
    import_propensity: float = Field(default=0.0, ge=0.0, le=0.50, description="Marginal propensity to import")
    max_rounds: int = Field(default=10, ge=3, le=20, description="Number of propagation rounds to compute")


class ISLMSimRequest(BaseModel):
    delta_r: float = Field(default=1.0, ge=-5.0, le=5.0, description="Policy interest rate shock (% points)")
    delta_g: float = Field(default=0.0, ge=-2000.0, le=2000.0, description="Fiscal shock to government spending")
    c: float = Field(default=0.75, ge=0.10, le=0.95, description="Marginal Propensity to Consume")
    b: float = Field(default=50.0, ge=1.0, le=200.0, description="Investment interest sensitivity (dI/dr)")
    k_y: float = Field(default=0.20, ge=0.01, le=1.0, description="Transaction money demand sensitivity (dL/dY)")
    h: float = Field(default=40.0, ge=1.0, le=200.0, description="Speculative money demand sensitivity (dL/dr)")
    c0: float = Field(default=200.0, ge=0.0)
    i0: float = Field(default=300.0, ge=0.0)
    g0: float = Field(default=500.0, ge=0.0)
    t0: float = Field(default=400.0, ge=0.0)
    m0: float = Field(default=600.0, ge=1.0)
    p: float = Field(default=1.0, ge=0.1)


# API Endpoints
@app.get("/api/status")
def get_system_status() -> dict[str, Any]:
    """Returns platform health, API connection states, and cache status."""
    has_fred_key = bool(FRED_API_KEY and FRED_API_KEY != "your_fred_api_key_here")
    return {
        "status": "online",
        "app_name": "EcoSim Macroeconomic Intelligence",
        "version": "2.0.0",
        "fred_integration": {
            "api_key_configured": has_fred_key,
            "direct_csv_fallback": True,
            "active_mode": "Official FRED API" if has_fred_key else "Official FRED Direct CSV Feed",
            "provider": "Federal Reserve Bank of St. Louis",
        },
        "world_bank_integration": {
            "key_required": False,
            "status": "Active (World Bank Open Data)",
            "provider": "World Bank Group",
        },
        "supported_countries_count": len(SUPPORTED_COUNTRIES),
    }


@app.get("/api/countries")
def get_countries() -> list[dict[str, Any]]:
    """Return all supported countries with region, flags, and data capabilities."""
    return data_service.get_supported_countries()


@app.get("/api/global/overview")
def get_global_overview() -> dict[str, Any]:
    """Return global macroeconomic KPI cards, multi-country rankings, and historical trends."""
    try:
        return data_service.get_global_overview()
    except Exception as e:
        logger.exception("Error generating global overview")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/country/{country_code}")
def get_country_profile(country_code: str) -> dict[str, Any]:
    """Return detailed economic profile and historical series for a selected country."""
    country_code = country_code.upper()
    if country_code not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Country '{country_code}' not supported.")
    try:
        return data_service.get_country_profile(country_code)
    except Exception as e:
        logger.exception("Error fetching country profile for %s", country_code)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/country/{country_code}/derived")
def get_derived_indicators(country_code: str) -> dict[str, Any]:
    """Return Misery Index and Real Interest Rate analysis for a selected country."""
    country_code = country_code.upper()
    if country_code not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Country '{country_code}' not supported.")
    try:
        return data_service.get_derived_indicators(country_code)
    except Exception as e:
        logger.exception("Error computing derived indicators for %s", country_code)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/forecast/ridge")
def run_ridge_forecast(req: RidgeForecastRequest) -> dict[str, Any]:
    """Run Phillips Curve Ridge regression inflation forecast with chronological evaluation."""
    try:
        return models_service.run_ridge_forecast(
            country_code=req.country_code,
            alpha=req.alpha,
            test_ratio=req.test_ratio,
            selected_features=req.features,
        )
    except Exception as e:
        logger.exception("Error running Ridge forecast")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulate/keynesian")
def simulate_keynesian(req: KeynesianSimRequest) -> dict[str, Any]:
    """Simulate Keynesian expenditure multiplier with round-by-round breakdown."""
    try:
        return simulation_service.simulate_keynesian(
            baseline_gdp=req.baseline_gdp,
            delta_g=req.delta_g,
            mpc=req.mpc,
            tax_rate=req.tax_rate,
            import_propensity=req.import_propensity,
            max_rounds=req.max_rounds,
        )
    except Exception as e:
        logger.exception("Error running Keynesian simulation")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulate/is-lm")
def simulate_is_lm(req: ISLMSimRequest) -> dict[str, Any]:
    """Simulate IS-LM goods and money market equilibrium shifts under policy shocks."""
    try:
        return simulation_service.simulate_is_lm(
            delta_r=req.delta_r,
            delta_g=req.delta_g,
            c=req.c,
            b=req.b,
            k_y=req.k_y,
            h=req.h,
            c0=req.c0,
            i0=req.i0,
            g0=req.g0,
            t0=req.t0,
            m0=req.m0,
            p=req.p,
        )
    except Exception as e:
        logger.exception("Error running IS-LM simulation")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/methodology")
def get_methodology() -> dict[str, Any]:
    """Return comprehensive econometric methodology, formulas, citations, and data documentation."""
    return {
        "data_sources": [
            {
                "name": "Federal Reserve Economic Data (FRED)",
                "organization": "Federal Reserve Bank of St. Louis",
                "coverage": "United States high-frequency macroeconomic time series",
                "frequency": "Monthly & Quarterly",
                "api_docs": "https://fred.stlouisfed.org/docs/api/fred/",
                "series": [
                    {"code": "GDPC1", "name": "Real Gross Domestic Product (SAAR, $B Chained 2017)", "freq": "Quarterly"},
                    {"code": "CPIAUCSL", "name": "Consumer Price Index for All Urban Consumers", "freq": "Monthly"},
                    {"code": "UNRATE", "name": "Civilian Unemployment Rate (%)", "freq": "Monthly"},
                    {"code": "FEDFUNDS", "name": "Federal Funds Effective Rate (%)", "freq": "Monthly"},
                    {"code": "GS10", "name": "10-Year Treasury Constant Maturity Yield (%)", "freq": "Monthly"},
                ],
            },
            {
                "name": "World Development Indicators (WDI)",
                "organization": "World Bank Group Open Data",
                "coverage": "Cross-country standardized macroeconomic indicators across 200+ nations",
                "frequency": "Annual",
                "api_docs": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
                "series": [
                    {"code": "NY.GDP.MKTP.CD", "name": "GDP in Current US$", "freq": "Annual"},
                    {"code": "NY.GDP.MKTP.KD", "name": "GDP in Constant 2015 US$", "freq": "Annual"},
                    {"code": "NY.GDP.PCAP.CD", "name": "GDP Per Capita in Current US$", "freq": "Annual"},
                    {"code": "NY.GDP.PCAP.KD", "name": "GDP Per Capita in Constant 2015 US$", "freq": "Annual"},
                    {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP Growth (Annual %)", "freq": "Annual"},
                    {"code": "FP.CPI.TOTL.ZG", "name": "Consumer Price Inflation (Annual %)", "freq": "Annual"},
                    {"code": "SL.UEM.TOTL.ZS", "name": "Unemployment Rate (% Total Labor Force)", "freq": "Annual"},
                    {"code": "NE.GDI.FTOT.ZS", "name": "Gross Fixed Capital Formation (% of GDP)", "freq": "Annual"},
                    {"code": "NE.CON.GOVT.ZS", "name": "General Government Final Consumption (% of GDP)", "freq": "Annual"},
                    {"code": "FR.INR.RINR", "name": "Real Interest Rate (%)", "freq": "Annual"},
                ],
            },
        ],
        "formulas": {
            "misery_index": "Misery Index = Inflation Rate (π) + Unemployment Rate (u)",
            "fisher_real_rate": "r ≈ i − π^e (Ex-Ante) or r ≈ i − π (Ex-Post Realized)",
            "ridge_regression": "min_{β} { ||y - Xβ||²₂ + λ ||β||²₂ } where λ ≥ 0 penalizes coefficient magnitude",
            "keynesian_multiplier": "ΔY = ΔG / (1 - MPC), or k_ext = 1 / [1 - MPC(1 - t) + m]",
            "is_curve": "Y = [C0 - c·T0 + I0 + G - b·r] / (1 - c)",
            "lm_curve": "r = [k_y·Y - (M/P)] / h",
        },
        "methodological_safeguards": [
            "Frequency Preservation: Quarterly forecasts are strictly computed from quarterly/monthly series (FRED). Annual World Bank series are modeled at annual horizon without unverified interpolation.",
            "Zero Lookahead Leakage: Chronological holdout splits are enforced without random shuffling. Feature scalers are fit strictly on training partitions.",
            "Empirical Association vs Causality: The Phillips Curve and Ridge forecasts represent empirical regularities and conditional expectations. In accordance with the Lucas Critique, historical statistical correlations do not establish invariant policy levers.",
            "Policy Simulation Nature: Keynesian multiplier and IS-LM simulations are pedagogical theoretical explorations with transparent assumptions, not commercial economic forecasts.",
        ],
        "academic_references": [
            "Hoerl, A. E., & Kennard, R. W. (1970). Ridge Regression: Biased Estimation for Nonorthogonal Problems. Technometrics, 12(1), 55-67.",
            "McCracken, M. W., & Ng, S. (2016). FRED-MD: A Monthly Database for Macroeconomic Research. Journal of Business & Economic Statistics, 34(4), 574-589.",
            "Medeiros, M. C., et al. (2021). Forecasting Inflation in a Data-Rich Environment: The Benefits of Machine Learning Methods. JBES, 39(1), 98-119.",
            "Phillips, A. W. (1958). The Relation Between Unemployment and the Rate of Change of Money Wage Rates in the United Kingdom, 1861-1957. Economica, 25(100), 283-299.",
            "Keynes, J. M. (1936). The General Theory of Employment, Interest, and Money. Macmillan.",
            "Hicks, J. R. (1937). Mr. Keynes and the 'Classics': A Suggested Interpretation. Econometrica, 5(2), 147-159.",
        ],
    }


# Mount built React frontend files at root (after all /api routes)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static_frontend")
