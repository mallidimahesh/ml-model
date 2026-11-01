"""Policy Simulation Engines for EcoSim: Keynesian Multiplier & IS-LM Framework.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


class SimulationService:
    """Provides analytical and numerical macroeconomic simulations."""

    def simulate_keynesian(
        self,
        baseline_gdp: float = 27800.0,
        delta_g: float = 250.0,
        mpc: float = 0.75,
        tax_rate: float = 0.0,
        import_propensity: float = 0.0,
        max_rounds: int = 10,
    ) -> dict[str, Any]:
        """Keynesian expenditure multiplier simulation with optional leakage extensions."""
        baseline_gdp = max(1.0, float(baseline_gdp))
        delta_g = float(delta_g)
        mpc = max(0.01, min(float(mpc), 0.98))
        tax_rate = max(0.0, min(float(tax_rate), 0.50))
        import_propensity = max(0.0, min(float(import_propensity), 0.50))

        # Basic Multiplier: k = 1 / (1 - MPC)
        basic_mps = 1.0 - mpc
        basic_multiplier = 1.0 / basic_mps

        # Extended Multiplier (with proportional income taxes & import leakage):
        # Y = C0 + c(1-t)Y + I + G + X - mY
        # k_ext = 1 / (1 - c(1-t) + m)
        denom_ext = 1.0 - mpc * (1.0 - tax_rate) + import_propensity
        extended_multiplier = 1.0 / denom_ext

        # Use extended if leakages are specified, otherwise basic
        has_leakages = (tax_rate > 0) or (import_propensity > 0)
        active_multiplier = extended_multiplier if has_leakages else basic_multiplier

        delta_y = delta_g * active_multiplier
        simulated_gdp = baseline_gdp + delta_y
        percent_change = (delta_y / baseline_gdp) * 100.0

        # Sequential round-by-round propagation
        effective_mpc = mpc * (1.0 - tax_rate) - import_propensity
        effective_mpc = max(0.0, effective_mpc)

        round_records = []
        cumulative = 0.0
        for r in range(1, max_rounds + 1):
            if r == 1:
                round_injection = delta_g
                desc = "Round 1: Initial Autonomous Expenditure Injection (ΔG)"
            else:
                round_injection = delta_g * (effective_mpc ** (r - 1))
                desc = f"Round {r}: Induced Domestic Consumption [c_eff^{r-1} × ΔG]"

            cumulative += round_injection
            pct_total = (cumulative / delta_y) * 100.0 if delta_y != 0 else 100.0

            round_records.append({
                "round": r,
                "description": desc,
                "round_addition": round(round_injection, 2),
                "cumulative_output": round(cumulative, 2),
                "percent_realized": round(min(100.0, pct_total), 1),
            })

        # Pedagogical explanation
        explanation = (
            f"Given a Marginal Propensity to Consume (MPC) of {mpc:.2f}, consumers spend {mpc*100:.0f}¢ of every extra dollar received, "
            f"saving {basic_mps*100:.0f}¢ (the Marginal Propensity to Save, MPS). "
            + (
                f"Accounting for proportional income tax of {tax_rate*100:.1f}% and import leakage of {import_propensity*100:.1f}%, "
                f"the effective expenditure multiplier is k_ext = 1 / [1 - {mpc:.2f}×(1 - {tax_rate:.2f}) + {import_propensity:.2f}] = {active_multiplier:.2f}. "
                if has_leakages
                else f"The simple theoretical multiplier is k = 1 / (1 - {mpc:.2f}) = {basic_multiplier:.2f}. "
            )
            + f"Consequently, an initial government spending shock of ΔG = ${delta_g:,.2f}B induces a cumulative output expansion "
            f"of ΔY = ${delta_y:,.2f}B, shifting national income from ${baseline_gdp:,.2f}B to ${simulated_gdp:,.2f}B ({percent_change:+.2f}%)."
        )

        return {
            "inputs": {
                "baseline_gdp": baseline_gdp,
                "delta_g": delta_g,
                "mpc": mpc,
                "tax_rate": tax_rate,
                "import_propensity": import_propensity,
                "has_leakages": has_leakages,
            },
            "results": {
                "basic_multiplier": round(basic_multiplier, 3),
                "extended_multiplier": round(extended_multiplier, 3),
                "active_multiplier": round(active_multiplier, 3),
                "delta_y": round(delta_y, 2),
                "simulated_gdp": round(simulated_gdp, 2),
                "percent_change": round(percent_change, 2),
                "mps": round(basic_mps, 3),
            },
            "round_breakdown": round_records,
            "explanation": explanation,
            "assumptions_disclaimer": (
                "Keynesian Multiplier Assumptions: (1) Rigid short-run prices (no immediate inflation response); "
                "(2) Sufficient spare economic capacity (unemployed labor and capital); "
                "(3) No monetary policy reaction (interest rates remain constant without central bank rate hikes); "
                "(4) Zero financial crowding out of private investment."
            ),
        }

    def simulate_is_lm(
        self,
        delta_r: float = 0.0,
        delta_g: float = 0.0,
        c: float = 0.75,
        b: float = 50.0,
        k_y: float = 0.20,
        h: float = 40.0,
        c0: float = 200.0,
        i0: float = 300.0,
        g0: float = 500.0,
        t0: float = 400.0,
        m0: float = 600.0,
        p: float = 1.0,
    ) -> dict[str, Any]:
        """Simulate goods and money market equilibrium under interest-rate and fiscal shocks."""
        c = max(0.10, min(float(c), 0.95))
        b = max(1.0, float(b))
        k_y = max(0.01, float(k_y))
        h = max(1.0, float(h))
        p = max(0.1, float(p))

        delta_r = float(delta_r)
        delta_g = float(delta_g)

        denom = b * k_y + h * (1.0 - c)

        # Baseline Equilibrium
        a_base = c0 - c * t0 + i0 + g0
        m_base = m0 / p
        y_base = (h * a_base + b * m_base) / denom
        r_base = (k_y * y_base - m_base) / h

        # Policy Shifted Equilibrium
        g_new = g0 + delta_g
        a_new = c0 - c * t0 + i0 + g_new
        r_new = r_base + delta_r

        # Along IS curve: Y_new = (A_new - b * r_new) / (1 - c)
        y_new = (a_new - b * r_new) / (1.0 - c)
        delta_y = y_new - y_base

        # Money market clearing condition: M_implied to sustain r_new at Y_new
        m_implied = (k_y * y_new - h * r_new) * p
        delta_m = m_implied - m0

        # Change in planned investment
        delta_i = -b * delta_r

        # Generate coordinate grid for IS and LM curves
        y_min = max(50.0, min(y_base, y_new) * 0.70)
        y_max = max(y_base, y_new) * 1.30
        y_grid = np.linspace(y_min, y_max, 60)

        # IS Curves: r = (A - (1 - c)*Y) / b
        r_is_base = (a_base - (1.0 - c) * y_grid) / b
        r_is_new = (a_new - (1.0 - c) * y_grid) / b

        # LM Curves: r = (k_y*Y - (M/P)) / h
        r_lm_base = (k_y * y_grid - m_base) / h
        r_lm_new = (k_y * y_grid - (m_implied / p)) / h

        curve_points = []
        for i, y_val in enumerate(y_grid):
            curve_points.append({
                "y": round(float(y_val), 1),
                "is_baseline": round(float(r_is_base[i]), 2),
                "is_policy": round(float(r_is_new[i]), 2),
                "lm_baseline": round(float(r_lm_base[i]), 2),
                "lm_policy": round(float(r_lm_new[i]), 2),
            })

        # Structured transmission mechanism narrative
        rate_direction = "Hawkish Tightening (+Δr)" if delta_r > 0 else ("Dovish Easing (−Δr)" if delta_r < 0 else "Neutral")
        output_direction = "contracts" if delta_y < 0 else ("expands" if delta_y > 0 else "remains constant")

        transmission_steps = [
            {
                "step": 1,
                "title": "Central Bank Policy Rate Decision",
                "description": f"The monetary authority shifts its policy target rate by {delta_r:+.2f}% points from r₀* = {r_base:.2f}% to r₁* = {r_new:.2f}% ({rate_direction}).",
            },
            {
                "step": 2,
                "title": "Investment Channel (IS Curve)",
                "description": f"With investment sensitivity b = {b:.1f}, commercial borrowing costs alter planned business investment by ΔI = −b·Δr = {delta_i:+.1f} units.",
            },
            {
                "step": 3,
                "title": "Goods-Market Output Adjustment",
                "description": f"Through the goods-market multiplier [1 / (1 − c) = {1.0/(1.0-c):.2f}], national output {output_direction} by ΔY = {delta_y:+.1f} units (from Y₀* = {y_base:.1f} to Y₁* = {y_new:.1f}).",
            },
            {
                "step": 4,
                "title": "Money Market Clearing (LM Liquidity)",
                "description": f"To sustain the target policy rate at the new equilibrium output, central bank operations endogenously adjust real money supply by ΔM = {delta_m:+.1f} units.",
            },
        ]

        preset_scenarios = [
            {
                "id": "hawkish_100",
                "name": "Hawkish Tightening (+100 bps)",
                "description": "Central bank curbs inflationary pressure with a +1.00% interest rate hike.",
                "delta_r": 1.0,
                "delta_g": 0.0,
            },
            {
                "id": "dovish_75",
                "name": "Dovish Rate Cut (−75 bps)",
                "description": "Counter-cyclical rate cut to stimulate private investment and economic activity.",
                "delta_r": -0.75,
                "delta_g": 0.0,
            },
            {
                "id": "fiscal_stimulus",
                "name": "Fiscal Stimulus (+100 Gov Spend)",
                "description": "Expansionary fiscal policy financed through borrowing while interest rates remain neutral.",
                "delta_r": 0.0,
                "delta_g": 100.0,
            },
            {
                "id": "policy_mix",
                "name": "Fiscal Stimulus + Rate Hike (Crowding Out)",
                "description": "Government expands spending by +150 while central bank hikes rates by +1.5% to prevent overheating.",
                "delta_r": 1.5,
                "delta_g": 150.0,
            },
        ]

        return {
            "baseline": {
                "y": round(float(y_base), 1),
                "r": round(float(r_base), 2),
                "m": round(float(m0), 1),
                "g": round(float(g0), 1),
            },
            "policy": {
                "y": round(float(y_new), 1),
                "r": round(float(r_new), 2),
                "m_implied": round(float(m_implied), 1),
                "g": round(float(g_new), 1),
            },
            "deltas": {
                "delta_y": round(float(delta_y), 1),
                "delta_r": round(float(delta_r), 2),
                "delta_m": round(float(delta_m), 1),
                "delta_g": round(float(delta_g), 1),
                "delta_i": round(float(delta_i), 1),
                "percent_y_change": round((delta_y / y_base) * 100.0, 2),
            },
            "parameters": {
                "c": c,
                "b": b,
                "k_y": k_y,
                "h": h,
                "p": p,
                "multiplier": round(1.0 / (1.0 - c), 2),
            },
            "curve_points": curve_points,
            "transmission_steps": transmission_steps,
            "preset_scenarios": preset_scenarios,
            "assumptions_disclaimer": (
                "IS-LM Framework Assumptions: (1) Fixed short-run general price level (P = 1.0); "
                "(2) Closed economy (no exchange rate or foreign trade flows); "
                "(3) Linear consumption, investment, and money demand schedules; "
                "(4) Central bank exogenously controls target interest rate r via liquidity operations."
            ),
        }


simulation_service = SimulationService()
