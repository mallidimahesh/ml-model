"""State Economic Stress Index Engine for EcoSim.

A transparent, documented analytical model measuring relative state-level economic vulnerability
across Indian States and Union Territories using genuine empirical observations.

Methodological Principles:
1. Grounded strictly in authentic empirical data from RBI DBIE and MoSPI PLFS.
2. Documented Min-Max Normalization preserving directional economic stress.
3. Explicit component weighting with mathematical contribution decomposition.
4. Robust handling of missing observations: NO national average imputation or fabricated values.
   States with fewer than 3 available components are explicitly excluded from rankings.
5. Pedagogical and analytical disclaimer: This index represents an experimental comparative
   analytical benchmark, NOT an official government rating or default probability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


# Explicit Component Definitions & Weighting Scheme
STRESS_COMPONENTS: dict[str, dict[str, Any]] = {
    "debt_gsdp_pct": {
        "name": "State Debt Burden (% of GSDP)",
        "source": "RBI State Finances: A Study of Budgets",
        "direction": "positive",  # Higher debt ratio -> higher fiscal vulnerability
        "default_weight": 0.25,
        "unit": "% of GSDP",
        "description": (
            "Total outstanding liabilities as a share of GSDP. Higher debt levels raise "
            "interest servicing burdens and restrict fiscal space for capital investment."
        ),
    },
    "plfs_ur": {
        "name": "Unemployment Rate (%)",
        "source": "MoSPI Periodic Labour Force Survey (PLFS)",
        "direction": "positive",  # Higher unemployment -> higher household stress
        "default_weight": 0.25,
        "unit": "% (Usual Status 15+)",
        "description": (
            "Proportion of labour force seeking work. Elevated unemployment signals labour "
            "market slack, suppressed household earnings, and underutilized human capital."
        ),
    },
    "cpi_inflation_yoy": {
        "name": "State CPI Combined Inflation (YoY %)",
        "source": "RBI DBIE / MoSPI Base 2012 Combined",
        "direction": "positive",  # Higher inflation -> higher purchasing power erosion
        "default_weight": 0.20,
        "unit": "% YoY",
        "description": (
            "Consumer price index inflation rate across combined rural and urban baskets. "
            "High price growth erodes real purchasing power, hitting low-income households hardest."
        ),
    },
    "gfd_gsdp_pct": {
        "name": "Gross Fiscal Deficit (% of GSDP)",
        "source": "RBI State Finances: A Study of Budgets",
        "direction": "positive",  # Higher fiscal deficit -> higher borrowing strain
        "default_weight": 0.15,
        "unit": "% of GSDP",
        "description": (
            "Net borrowing requirement to finance state expenditures relative to GSDP. "
            "Deficits exceeding FRBM benchmarks (3.0%–3.5%) risk debt unsustainability."
        ),
    },
    "real_growth_yoy": {
        "name": "Real State Output Growth (YoY %)",
        "source": "RBI Handbook of Statistics / MoSPI NAS",
        "direction": "inverted",  # Lower economic growth -> higher economic stress
        "default_weight": 0.15,
        "unit": "% YoY (Constant Prices)",
        "description": (
            "Annual percentage change in Net State Domestic Product at constant 2011-12 prices. "
            "Weak or contracting output restricts tax buoyancy and employment generation."
        ),
    },
}


@dataclass
class StateStressResult:
    """Detailed score calculation and component breakdown for a state."""

    state: str
    state_code: str
    region: str
    stress_score: float | None
    stress_tier: str
    is_eligible_for_ranking: bool
    components_available_count: int
    total_components_count: int
    coverage_ratio: float
    component_raw_values: dict[str, float | None]
    component_normalized_scores: dict[str, float | None]
    component_contributions: dict[str, float | None]
    component_observation_years: dict[str, str]
    eligibility_note: str


def compute_state_economic_stress_index(
    df_snapshot: pd.DataFrame,
    custom_weights: dict[str, float] | None = None,
    min_components_required: int = 3,
) -> tuple[pd.DataFrame, list[StateStressResult]]:
    """Calculates normalized State Economic Stress Index using strictly available empirical series.

    Args:
        df_snapshot: Master snapshot DataFrame from IndiaStateDataClient.
        custom_weights: Optional overrides for default component weights.
        min_components_required: Minimum available non-null indicators for ranking eligibility.

    Returns:
        tuple: (df_ranked, list of detailed StateStressResult)
    """
    df = df_snapshot.copy()
    weights = {k: v["default_weight"] for k, v in STRESS_COMPONENTS.items()}
    if custom_weights:
        weights.update(custom_weights)

    # Normalize weights so they sum to 1.0 across the 5 indicators
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    # Calculate min and max across all empirical observations for Min-Max Scaling
    min_max_bounds: dict[str, tuple[float, float]] = {}
    for comp_key, comp_meta in STRESS_COMPONENTS.items():
        if comp_key in df.columns:
            valid_vals = df[comp_key].dropna().values
            if len(valid_vals) > 0:
                min_max_bounds[comp_key] = (float(np.min(valid_vals)), float(np.max(valid_vals)))
            else:
                min_max_bounds[comp_key] = (0.0, 1.0)

    results: list[StateStressResult] = []
    summary_rows: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        sname = str(row["state"])
        scode = str(row.get("state_code", ""))
        region = str(row.get("region", "Other"))

        raw_vals: dict[str, float | None] = {}
        norm_scores: dict[str, float | None] = {}
        contribs: dict[str, float | None] = {}
        ref_years: dict[str, str] = {}

        available_keys: list[str] = []

        for comp_key, comp_meta in STRESS_COMPONENTS.items():
            val = row.get(comp_key)
            if pd.notna(val):
                raw_val = float(val)
                raw_vals[comp_key] = raw_val
                available_keys.append(comp_key)

                # Min-Max Normalization (0 - 100)
                mn, mx = min_max_bounds[comp_key]
                span = mx - mn if abs(mx - mn) > 1e-6 else 1.0

                if comp_meta["direction"] == "positive":
                    # Higher value = Higher Stress
                    z = ((raw_val - mn) / span) * 100.0
                else:
                    # Inverted: Lower value = Higher Stress
                    z = ((mx - raw_val) / span) * 100.0

                z_clamped = max(0.0, min(100.0, z))
                norm_scores[comp_key] = z_clamped

                # Extract reference year if present in row
                yr_col = {
                    "debt_gsdp_pct": "debt_ref_yr",
                    "plfs_ur": "plfs_ref_yr",
                    "cpi_inflation_yoy": "cpi_ref_period",
                    "gfd_gsdp_pct": "debt_ref_yr",
                    "real_growth_yoy": "growth_ref_yr",
                }.get(comp_key, "")
                ref_years[comp_key] = str(row.get(yr_col, "Latest Observed"))
            else:
                raw_vals[comp_key] = None
                norm_scores[comp_key] = None
                ref_years[comp_key] = "Data Unavailable"

        m_count = len(available_keys)
        total_k = len(STRESS_COMPONENTS)
        coverage_ratio = m_count / total_k

        # Strict missing value handling: NO national average substitution
        if m_count >= min_components_required:
            is_eligible = True
            # Weighted average strictly over available components
            active_weight_sum = sum(weights[k] for k in available_keys)
            score = 0.0
            for k in available_keys:
                # Relative contribution C_{i,k} = (w_k * z_{i,k}) / sum_{j in A} w_j
                effective_w = weights[k] / active_weight_sum
                c_val = effective_w * norm_scores[k]
                contribs[k] = c_val
                score += c_val

            for k in STRESS_COMPONENTS:
                if k not in available_keys:
                    contribs[k] = None

            # Stress Tiers
            if score < 35.0:
                tier = "Low Economic Vulnerability"
            elif score < 50.0:
                tier = "Moderate Vulnerability"
            elif score < 65.0:
                tier = "Elevated Vulnerability"
            else:
                tier = "High Relative Stress"

            note = f"Score computed across {m_count}/{total_k} available empirical components."
        else:
            is_eligible = False
            score = None
            tier = "Insufficient Data Coverage"
            for k in STRESS_COMPONENTS:
                contribs[k] = None
            note = (
                f"Excluded from rankings: Only {m_count}/{total_k} indicators observable "
                f"(minimum {min_components_required} required for valid aggregation)."
            )

        res = StateStressResult(
            state=sname,
            state_code=scode,
            region=region,
            stress_score=score,
            stress_tier=tier,
            is_eligible_for_ranking=is_eligible,
            components_available_count=m_count,
            total_components_count=total_k,
            coverage_ratio=coverage_ratio,
            component_raw_values=raw_vals,
            component_normalized_scores=norm_scores,
            component_contributions=contribs,
            component_observation_years=ref_years,
            eligibility_note=note,
        )
        results.append(res)

        summary_rows.append({
            "state": sname,
            "state_code": scode,
            "region": region,
            "stress_score": score,
            "stress_tier": tier,
            "is_eligible": is_eligible,
            "components_count": f"{m_count}/{total_k}",
            "coverage_pct": round(coverage_ratio * 100, 1),
            "debt_gsdp_pct": raw_vals.get("debt_gsdp_pct"),
            "plfs_ur": raw_vals.get("plfs_ur"),
            "cpi_inflation_yoy": raw_vals.get("cpi_inflation_yoy"),
            "gfd_gsdp_pct": raw_vals.get("gfd_gsdp_pct"),
            "real_growth_yoy": raw_vals.get("real_growth_yoy"),
            "eligibility_note": note,
        })

    df_summary = pd.DataFrame(summary_rows)

    # Rank eligible states: Higher score = Higher Stress
    eligible = df_summary[df_summary["is_eligible"]].copy()
    ineligible = df_summary[~df_summary["is_eligible"]].copy()

    eligible = eligible.sort_values("stress_score", ascending=False).reset_index(drop=True)
    eligible["stress_rank"] = range(1, len(eligible) + 1)

    ineligible["stress_rank"] = np.nan

    df_ranked = pd.concat([eligible, ineligible], ignore_index=True)
    return df_ranked, results
