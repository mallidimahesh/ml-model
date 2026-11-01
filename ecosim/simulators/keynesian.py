"""Keynesian Government-Spending Multiplier Simulator for EcoSim.

Calculates change in output using the classical formula:
    Change in Output (ΔY) = Change in Government Spending (ΔG) / (1 - MPC)
"""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class KeynesianSimulationResult:
    """Results from Keynesian government-spending simulation."""

    mpc: float
    mps: float
    multiplier: float
    delta_g: float
    delta_y: float
    rounds_breakdown: pd.DataFrame
    explanation: str


def simulate_keynesian_multiplier(
    delta_g: float,
    mpc: float,
    max_rounds: int = 8,
) -> KeynesianSimulationResult:
    """Compute the Keynesian expenditure multiplier and round-by-round output expansion.

    Formula:
        k = 1 / (1 - MPC)
        ΔY = ΔG / (1 - MPC)

    Args:
        delta_g: Change in government expenditure ($ billions).
        mpc: Marginal Propensity to Consume (0 < MPC < 1).
        max_rounds: Number of sequential consumption rounds to detail.

    Returns:
        KeynesianSimulationResult object.
    """
    if not (0.0 < mpc < 1.0):
        raise ValueError(f"Marginal Propensity to Consume (MPC) must be strictly between 0 and 1. Received {mpc}.")

    mps = 1.0 - mpc
    multiplier = 1.0 / mps
    delta_y = delta_g * multiplier

    # Build sequential round-by-round progression
    round_records = []
    cumulative_spend = 0.0

    for r in range(1, max_rounds + 1):
        if r == 1:
            round_injection = delta_g
            round_desc = "Initial Government Spending (ΔG)"
        else:
            round_injection = delta_g * (mpc ** (r - 1))
            round_desc = f"Round {r} Induced Consumer Spending (MPC^{r-1} × ΔG)"

        cumulative_spend += round_injection
        round_records.append({
            "Round": r,
            "Description": round_desc,
            "Round Addition (₹B)": round(round_injection, 2),
            "Cumulative Output (₹B)": round(cumulative_spend, 2),
            "% of Final Impact": round((cumulative_spend / delta_y) * 100, 1) if delta_y != 0 else 100.0,
        })

    df_rounds = pd.DataFrame(round_records)

    explanation = (
        f"With an MPC of {mpc:.2f}, households spend {mpc*100:.1f}% of every extra rupee received "
        f"and save {mps*100:.1f}% (the Marginal Propensity to Save, MPS). "
        f"The resulting expenditure multiplier is k = 1 / (1 - {mpc:.2f}) = {multiplier:.2f}. "
        f"An injection of ₹{delta_g:,.2f}B in government spending generates a total output expansion "
        f"of ΔY = ₹{delta_y:,.2f}B across all subsequent economic rounds."
    )

    return KeynesianSimulationResult(
        mpc=mpc,
        mps=mps,
        multiplier=multiplier,
        delta_g=delta_g,
        delta_y=delta_y,
        rounds_breakdown=df_rounds,
        explanation=explanation,
    )
