"""Predictive modeling & analytical indices package for EcoSim (Ridge Regression only).
"""

from ecosim.models.ridge_model import MacroRidgeForecaster, RidgeEvaluationResults
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

__all__ = [
    "MacroRidgeForecaster",
    "RidgeEvaluationResults",
    "IndiaMultiForecaster",
    "TargetEvaluationResult",
    "compute_state_economic_stress_index",
    "StateStressResult",
    "STRESS_COMPONENTS",
    "US_NBER_RECESSIONS",
    "INDIA_SLOWDOWN_REGIMES",
    "get_nber_recessions",
    "get_india_slowdowns",
    "classify_us_regimes",
    "compute_us_regime_statistics",
    "compute_india_slowdown_statistics",
    "validate_monthly_continuity",
    "calculate_mom_yoy_inflation",
    "decompose_monthly_inflation_classical",
    "detect_inflation_turning_points",
    "load_india_quarterly_phillips_dataset",
]
