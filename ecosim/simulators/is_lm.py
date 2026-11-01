"""Simplified IS-LM Macroeconomic Policy Simulator for EcoSim.

Models the interaction between the goods market (IS curve) and money market (LM curve)
to evaluate equilibrium national output (Y) and interest rate (r) under interest-rate
and fiscal policy shocks.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class ISLMSimulationResult:
    """Equilibrium, parameter assumptions, and coordinates for baseline and policy scenarios."""

    y_base: float
    r_base: float
    y_new: float
    r_new: float
    delta_y: float
    delta_r: float
    delta_g: float
    delta_m: float
    c: float
    b: float
    k_y: float
    h: float
    p: float
    a_base: float
    m_base: float
    m_implied: float
    curve_df: pd.DataFrame
    explanation: str
    transmission_steps: list[str]


def simulate_is_lm(
    delta_g: float = 0.0,
    delta_r: float = 0.0,
    c: float = 0.75,          # Marginal propensity to consume (MPC)
    b: float = 50.0,          # Investment sensitivity to interest rate (dI/dr)
    k_y: float = 0.20,        # Transaction demand for money sensitivity (dL/dY)
    h: float = 40.0,          # Speculative money demand sensitivity (dL/dr)
    c0: float = 200.0,        # Autonomous consumption
    i0: float = 300.0,        # Autonomous investment
    g0: float = 500.0,        # Baseline government spending
    t0: float = 400.0,        # Lump-sum taxes
    m0: float = 600.0,        # Baseline real money supply (M/P)
    p: float = 1.0,           # Fixed short-run price level
) -> ISLMSimulationResult:
    """Simulate Goods-Market (IS) and Money-Market (LM) equilibrium under policy interest-rate shocks.

    Theoretical Framework:
    - IS Curve (Goods Market Equilibrium):
        Y = C + I + G = [C0 + c(Y - T0)] + [I0 - b*r] + G
        r_IS = (A - (1 - c)*Y) / b
        where Autonomous Expenditure A = C0 - c*T0 + I0 + G
    - LM Curve (Money Market Equilibrium):
        (M/P) = k_y * Y - h * r
        r_LM = (k_y * Y - (M/P)) / h
    - Baseline Simultaneous Equilibrium (Y*, r*):
        Y* = [h*A_base + b*(M_base)] / [b*k_y + h*(1 - c)]
        r* = [k_y * Y* - M_base] / h
    - Policy Interest-Rate Shock (Δr):
        The central bank shifts its target policy rate: r_new = r* + Δr.
        Along the goods market (IS curve), investment adjusts:
        Y_new = [A_new - b * r_new] / (1 - c)
        ΔY = -[b / (1 - c)] * Δr
        To sustain r_new at output Y_new, the money supply endogenously adjusts to:
        (M_implied / P) = k_y * Y_new - h * r_new

    Args:
        delta_g: Fiscal policy shock (change in government expenditure, $B).
        delta_r: Interest rate shock (change in policy interest rate, percentage points).
        c: Marginal Propensity to Consume (0 < c < 1).
        b: Interest sensitivity of investment (> 0).
        k_y: Income sensitivity of money demand (> 0).
        h: Interest sensitivity of money demand (> 0).

    Returns:
        ISLMSimulationResult with equilibria, coordinates, parameters, and transmission narrative.
    """
    if not (0.0 < c < 1.0):
        raise ValueError("MPC (c) must be between 0 and 1.")
    if b <= 0 or k_y <= 0 or h <= 0 or p <= 0:
        raise ValueError("Model parameters b, k_y, h, and P must be strictly positive.")

    denom = b * k_y + h * (1.0 - c)

    # 1. Baseline Equilibrium (ΔG = 0, Δr = 0)
    a_base = c0 - c * t0 + i0 + g0
    m_base = m0 / p
    y_base = (h * a_base + b * m_base) / denom
    r_base = (k_y * y_base - m_base) / h

    # 2. Policy-Shifted Equilibrium under Interest Rate Shock (Δr) and Fiscal Shock (ΔG)
    g_new = g0 + delta_g
    a_new = c0 - c * t0 + i0 + g_new
    r_new = r_base + delta_r

    # In Goods Market (IS curve): Y = (A_new - b * r_new) / (1 - c)
    y_new = (a_new - b * r_new) / (1.0 - c)

    # In Money Market (LM curve): M_implied to sustain r_new at Y_new
    m_implied = (k_y * y_new - h * r_new) * p
    delta_m = m_implied - m0

    delta_y = y_new - y_base

    # Generate curve coordinate ranges for visualization
    y_min = max(100.0, min(y_base, y_new) * 0.70)
    y_max = max(y_base, y_new) * 1.30
    y_grid = np.linspace(y_min, y_max, 100)

    # IS curves: r = (A - (1 - c)*Y) / b
    r_is_base = (a_base - (1.0 - c) * y_grid) / b
    r_is_new = (a_new - (1.0 - c) * y_grid) / b

    # LM curves: r = (k_y*Y - (M/P)) / h
    r_lm_base = (k_y * y_grid - m_base) / h
    r_lm_new = (k_y * y_grid - (m_implied / p)) / h

    curve_df = pd.DataFrame({
        "Y": y_grid,
        "IS_Baseline": r_is_base,
        "IS_Policy": r_is_new,
        "LM_Baseline": r_lm_base,
        "LM_Policy": r_lm_new,
    })

    # Structured economic transmission steps
    direction_rate = "tightening (+Δr)" if delta_r > 0 else ("easing (−Δr)" if delta_r < 0 else "neutral (Δr = 0)")
    direction_output = "contracts" if delta_y < 0 else ("expands" if delta_y > 0 else "remains unchanged")

    transmission_steps = [
        f"<b>1. Central Bank Shock:</b> Policy interest rate shifted by {delta_r:+.2f}% points from baseline r₀* = {r_base:.2f}% to r₁* = {r_new:.2f}% ({direction_rate}).",
        f"<b>2. Investment Channel (IS Curve):</b> With investment sensitivity b = {b:.1f}, planned investment moves along the IS curve, changing by ΔI = −b·Δr = {(-b * delta_r):+.1f} ₹B.",
        f"<b>3. Output Multiplier:</b> Through the Keynesian goods-market multiplier [1 / (1 − c) = {1.0/(1.0-c):.2f}], equilibrium national output {direction_output} by ΔY = {delta_y:+.1f} ₹B (from {y_base:.1f} to {y_new:.1f}).",
        f"<b>4. Money Market Liquidity (LM Curve):</b> To support the target policy rate at the new output level, money supply endogenously adjusts to M₁ = {m_implied:.1f} (ΔM = {delta_m:+.1f} ₹B).",
    ]

    explanation = (
        f"The central bank imposes an interest rate shock of Δr = {delta_r:+.2f}% points. "
        f"Along the IS curve, higher borrowing costs depress investment by {-b * delta_r:+.1f} ₹B, "
        f"leading to a total output change of ΔY = {delta_y:+.1f} ₹B in goods-market equilibrium. "
        f"The money supply adjusts endogenously by ΔM = {delta_m:+.1f} ₹B to clear money demand at the target policy rate."
    )

    return ISLMSimulationResult(
        y_base=float(y_base),
        r_base=float(r_base),
        y_new=float(y_new),
        r_new=float(r_new),
        delta_y=float(delta_y),
        delta_r=float(delta_r),
        delta_g=float(delta_g),
        delta_m=float(delta_m),
        c=float(c),
        b=float(b),
        k_y=float(k_y),
        h=float(h),
        p=float(p),
        a_base=float(a_base),
        m_base=float(m_base),
        m_implied=float(m_implied),
        curve_df=curve_df,
        explanation=explanation,
        transmission_steps=transmission_steps,
    )
