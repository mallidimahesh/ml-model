"""Configuration constants, API endpoints, and macroeconomic series identifiers for EcoSim.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load local environment variables if available
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# FRED API Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_OBSERVATIONS_URL = f"{FRED_BASE_URL}/series/observations"

# Approved FRED Macroeconomic Series IDs
FRED_SERIES = {
    "GDP": {
        "id": "GDPC1",
        "name": "Real Gross Domestic Product",
        "frequency": "Quarterly",
        "units": "Billions of Chained Rupees (₹B, Converted @ ₹83/USD)",
        "description": "Inflation-adjusted measure of total domestic output produced, converted to Indian Rupees (₹B).",
    },
    "CPI": {
        "id": "CPIAUCSL",
        "name": "Consumer Price Index (CPI-U)",
        "frequency": "Monthly",
        "units": "Index 1982-1984=100",
        "description": "Price changes across a basket of consumer goods and services.",
    },
    "UNEMPLOYMENT": {
        "id": "UNRATE",
        "name": "Civilian Unemployment Rate",
        "frequency": "Monthly",
        "units": "Percent",
        "description": "Percentage of civilian labor force currently without work.",
    },
    "FEDFUNDS": {
        "id": "FEDFUNDS",
        "name": "Federal Funds Effective Rate",
        "frequency": "Monthly",
        "units": "Percent",
        "description": "Interest rate at which depository institutions trade federal funds overnight.",
    },
    "TREASURY_10Y": {
        "id": "GS10",
        "name": "10-Year Treasury Constant Maturity Rate",
        "frequency": "Monthly",
        "units": "Percent",
        "description": "Yield on 10-year US Treasury debt, standard benchmark for long-term borrowing costs.",
    },
}

# World Bank API Configuration (No API key required)
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

# Approved World Bank Indicator Codes
WORLD_BANK_INDICATORS = {
    "GDP_GROWTH": {
        "code": "NY.GDP.MKTP.KD.ZG",
        "name": "GDP Growth (Annual %)",
        "frequency": "Annual",
    },
    "INFLATION": {
        "code": "FP.CPI.TOTL.ZG",
        "name": "Inflation, Consumer Prices (Annual %)",
        "frequency": "Annual",
    },
    "UNEMPLOYMENT": {
        "code": "SL.UEM.TOTL.ZS",
        "name": "Unemployment (% of Total Labor Force)",
        "frequency": "Annual",
    },
}

# Indian Macroeconomic Data Configurations (RBI DBIE & MoSPI eSankhyiki)
RBI_DBIE_BASE_URL = os.getenv("RBI_DBIE_BASE_URL", "https://data-api.dbie.rbihub.in").rstrip("/")
MOSPI_API_BASE_URL = os.getenv("MOSPI_API_BASE_URL", "https://api.mospi.gov.in").rstrip("/")
MOSPI_API_TOKEN = os.getenv("MOSPI_API_TOKEN", "").strip()

INDIAN_MACRO_SERIES = {
    "CPI": {
        "source": "RBI DBIE & MoSPI",
        "table": "real_sector.cpi_ruc_rn",
        "code": "C_GIAG (All India Combined)",
        "name": "Consumer Price Index (Combined All-India)",
        "frequency": "Monthly",
        "units": "Base 2012=100 / % YoY Inflation",
        "description": "Headline consumer price inflation across rural, urban, and combined All-India baskets.",
    },
    "REAL_GDP": {
        "source": "RBI DBIE",
        "table": "real_sector.qtr_gdp_mrkt_prc_rn",
        "code": "CEXP_GDP_MARK_CST",
        "name": "Quarterly Real GDP at Constant 2011-12 Prices",
        "frequency": "Quarterly",
        "units": "₹ Crores / % YoY Growth",
        "description": "Total inflation-adjusted market value of all final goods and services produced domestically.",
    },
    "IIP": {
        "source": "RBI DBIE & MoSPI",
        "table": "real_sector.inx_inds_prod_rn",
        "code": "SEC_GEN_INDX",
        "name": "Index of Industrial Production (General Index)",
        "frequency": "Monthly",
        "units": "Base 2011-12=100 / % YoY Growth",
        "description": "Physical volume of industrial output covering Mining, Manufacturing, and Electricity.",
    },
    "WACR": {
        "source": "RBI DBIE",
        "table": "financial_markets.war_call_money_rn",
        "code": "AVERAGE_RATE (WACR)",
        "name": "Weighted Average Call Money Rate",
        "frequency": "Monthly",
        "units": "Percent Annualized (% p.a.)",
        "description": "RBI's operational monetary policy rate representing overnight unsecured interbank borrowing costs.",
    },
}

# Indian State-Level Economic Series Metadata
INDIAN_STATE_SERIES = {
    "PER_CAPITA_NSDP_CURR": {
        "source": "RBI Handbook of Statistics on Indian Economy",
        "table": "real_sector.r227_per_capita_net_state_domestic_product_state_wise_at_curren",
        "name": "Per Capita Net State Domestic Product (Current Prices)",
        "frequency": "Annual - Financial Year",
        "units": "Indian Rupees (₹)",
        "coverage": "33 States & Union Territories (Base 2011-12)",
    },
    "PER_CAPITA_NSDP_CONST": {
        "source": "RBI Handbook of Statistics on Indian Economy",
        "table": "real_sector.r250_per_capita_net_state_domestic_product_state_wise_at_consta",
        "name": "Per Capita Net State Domestic Product (Constant 2011-12 Prices)",
        "frequency": "Annual - Financial Year",
        "units": "Indian Rupees (₹)",
        "coverage": "33 States & Union Territories (Base 2011-12)",
    },
    "NSDP_CURR": {
        "source": "RBI Handbook of Statistics on Indian Economy",
        "table": "real_sector.r65_net_state_domestic_product_state_wise_at_current_prices",
        "name": "Net State Domestic Product (Current Prices)",
        "frequency": "Annual - Financial Year",
        "units": "₹ Crores",
        "coverage": "33 States & Union Territories (Base 2011-12)",
    },
    "NSDP_CONST": {
        "source": "RBI Handbook of Statistics on Indian Economy",
        "table": "real_sector.r66_net_state_domestic_product_state_wise_at_constant_prices",
        "name": "Net State Domestic Product (Constant 2011-12 Prices)",
        "frequency": "Annual - Financial Year",
        "units": "₹ Crores / % YoY Real Growth",
        "coverage": "33 States & Union Territories (Base 2011-12)",
    },
    "STATE_DEBT": {
        "source": "RBI State Finances: A Study of Budgets",
        "table": "public_finance.st_fin_std_budgets_rn",
        "code": "TOTOUT_LIA_PT_GSDP",
        "name": "Total Outstanding Liabilities as % of GSDP",
        "frequency": "Annual - Financial Year",
        "units": "Percent of GSDP (%)",
        "coverage": "32 States & Union Territories",
    },
    "STATE_GFD": {
        "source": "RBI State Finances: A Study of Budgets",
        "table": "public_finance.st_fin_std_budgets_rn",
        "code": "GFD_GSDP",
        "name": "Gross Fiscal Deficit as % of GSDP",
        "frequency": "Annual - Financial Year",
        "units": "Percent of GSDP (%)",
        "coverage": "32 States & Union Territories",
    },
    "STATE_CPI": {
        "source": "RBI DBIE & MoSPI",
        "table": "real_sector.cpi_ruc_st_rn",
        "code": "C_GIAG (All-India Combined)",
        "name": "State-Level Consumer Price Index Combined (Base 2012=100)",
        "frequency": "Monthly",
        "units": "Index / % YoY Inflation",
        "coverage": "36 States & Union Territories",
    },
    "PLFS_LABOUR": {
        "source": "MoSPI NSSO Periodic Labour Force Survey (PLFS)",
        "table": "Annual Reports Table 1 (LFPR), Table 2 (WPR), Table 4 (UR)",
        "name": "State-Level Labour Force Indicators (Age 15+, Usual Status ps+ss)",
        "frequency": "Annual Survey Round (July–June)",
        "units": "Percent of Population / Labour Force (%)",
        "coverage": "All 36 States & Union Territories",
    },
}

# Academic & Pedagogical Disclaimers
DISCLAIMERS = {
    "DATA_SOURCE_NOTE": (
        "Live data fetched from Federal Reserve Economic Data (FRED), World Bank Open Data, "
        "RBI Database on Indian Economy (DBIE), and MoSPI eSankhyiki / PLFS publications. "
        "Series frequencies differ (monthly, quarterly, annual) and are explicitly harmonized."
    ),
    "SIMULATION_LIMITATION": (
        "Policy simulations (Keynesian Multiplier and IS-LM) are stylized theoretical models "
        "designed for academic demonstration. They do not constitute guaranteed macroeconomic forecasts."
    ),
    "ML_MODEL_NOTE": (
        "Statistical forecasts utilize Ridge Regression with strictly chronological train/test splits. "
        "All features are lagged or contemporaneous at origin to prevent lookahead data leakage. "
        "Models are evaluated against simple empirical persistence baselines."
    ),
    "STATE_STRESS_DISCLAIMER": (
        "The State Economic Stress Index is an experimental analytical metric designed for comparative "
        "macroeconomic analysis across Indian states. It does not constitute an official government rating, "
        "sovereign credit grade, or default probability."
    ),
    "REGIME_ANALYSIS_NOTE": (
        "Recession intervals for the United States are derived from the official National Bureau of Economic "
        "Research (NBER) Business Cycle Dating Committee chronology. For India, which has no official recession-dating "
        "body, analytical slowdown regimes are determined via a transparent, reproducible rule (>= 2 consecutive "
        "quarters of below-5% Real GDP growth or contraction). These descriptive statistics do not imply causality."
    ),
    "INFLATION_DECOMPOSITION_NOTE": (
        "Classical time series decomposition separates monthly CPI into a 2x12 centered moving average trend, "
        "a zero-sum 12-month normalized seasonal component, and an irregular residual. The algorithm requires "
        "strictly contiguous monthly observations without unverified interpolation."
    ),
    "PHILLIPS_CURVE_CAUSALITY_NOTE": (
        "The empirical Phillips Curve scatter plot and OLS regression illustrate an observational statistical "
        "association between unemployment and inflation. In accordance with the Lucas Critique and modern macro theory "
        "(Friedman-Phelps expectations-augmented model), this statistical correlation does not establish an exploitable "
        "policy trade-off or permanent causal mechanism."
    ),
    "WORLD_BANK_COMPARABILITY_NOTE": (
        "World Bank Open Data indicators (GDP growth, CPI inflation, and unemployment) are annual national metrics. "
        "Cross-country comparisons are evaluated across verified common calendar years to ensure balanced, "
        "unbiased international macroeconomic analysis."
    ),
}
