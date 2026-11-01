"""Interactive Plotly visualization components for EcoSim.
"""

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

__all__ = [
    "plot_macro_overview",
    "plot_multi_series_selector",
    "plot_actual_vs_predicted",
    "plot_feature_coefficients",
    "plot_phillips_curve",
    "plot_keynesian_rounds",
    "plot_is_lm_curves",
    "plot_world_bank_indicator",
    "plot_india_target_forecast",
    "plot_india_model_comparison",
    "plot_india_coefficients",
    "plot_inflation_decomposition",
    "plot_inflation_turning_points",
    "plot_regime_comparison_bars",
    "plot_world_bank_multi_country",
    "plot_world_bank_league_table",
    "add_nber_recession_bands",
    "apply_terminal_theme",
    "plot_state_ranking_barchart",
    "plot_state_historical_trends",
    "plot_stress_index_breakdown",
    "plot_stress_quadrant",
]
