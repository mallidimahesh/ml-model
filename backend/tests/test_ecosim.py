"""Unit and integration tests for EcoSim backend.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.simulation_service import simulation_service
from backend.models_service import models_service

client = TestClient(app)


def test_system_status():
    """Verify system status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "fred_integration" in data
    assert "world_bank_integration" in data


def test_get_countries():
    """Verify supported countries list."""
    response = client.get("/api/countries")
    assert response.status_code == 200
    countries = response.json()
    assert len(countries) >= 10
    codes = [c["code"] for c in countries]
    assert "USA" in codes
    assert "IND" in codes
    assert "CHN" in codes


def test_global_overview():
    """Verify global overview KPIs and rankings."""
    response = client.get("/api/global/overview")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert len(data["kpis"]) >= 5
    assert "rankings" in data
    assert "historical_trends" in data


def test_country_profile():
    """Verify country profile for USA and India."""
    for c_code in ["USA", "IND"]:
        response = client.get(f"/api/country/{c_code}")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "latest" in data
        assert "policy_rate" in data
        assert "series" in data


def test_derived_indicators():
    """Verify Misery Index and Real Interest Rate calculations."""
    response = client.get("/api/country/USA/derived")
    assert response.status_code == 200
    data = response.json()
    assert "misery_index" in data
    assert "real_interest_rate" in data
    assert data["misery_index"]["value"] is not None
    assert data["real_interest_rate"]["ex_post_real_rate"] is not None


def test_keynesian_multiplier_basic():
    """Verify basic Keynesian multiplier formula: k = 1 / (1 - MPC)."""
    res = simulation_service.simulate_keynesian(
        baseline_gdp=1000.0,
        delta_g=100.0,
        mpc=0.80,
    )
    assert round(res["results"]["basic_multiplier"], 2) == 5.0
    assert round(res["results"]["delta_y"], 2) == 500.0
    assert round(res["results"]["simulated_gdp"], 2) == 1500.0
    assert len(res["round_breakdown"]) == 10


def test_keynesian_multiplier_extended():
    """Verify extended Keynesian multiplier with tax and import leakages."""
    res = simulation_service.simulate_keynesian(
        baseline_gdp=1000.0,
        delta_g=100.0,
        mpc=0.80,
        tax_rate=0.20,
        import_propensity=0.10,
    )
    # k_ext = 1 / (1 - 0.8*(1-0.2) + 0.1) = 1 / (1 - 0.64 + 0.1) = 1 / 0.46 = 2.174
    expected_k = 1.0 / (1.0 - 0.80 * (1.0 - 0.20) + 0.10)
    assert abs(res["results"]["active_multiplier"] - expected_k) < 0.01


def test_is_lm_simulation():
    """Verify IS-LM equilibrium solving."""
    res = simulation_service.simulate_is_lm(
        delta_r=1.0,
        delta_g=0.0,
        c=0.75,
        b=50.0,
        k_y=0.20,
        h=40.0,
    )
    assert res["baseline"]["y"] > 0
    assert res["baseline"]["r"] is not None
    # With delta_r = +1.0, delta_y should be -b/(1-c) * delta_r = -50 / 0.25 * 1.0 = -200
    assert abs(res["deltas"]["delta_y"] - (-200.0)) < 0.1
    assert len(res["curve_points"]) == 60
    assert len(res["transmission_steps"]) == 4


def test_ridge_forecast_quarterly():
    """Verify Ridge regression on quarterly FRED data."""
    res = models_service.run_ridge_forecast(
        country_code="USA",
        alpha=1.0,
        test_ratio=0.20,
    )
    assert res["frequency"] == "Quarterly"
    assert res["metrics"]["test_rmse"] > 0
    assert res["metrics"]["baseline_rmse"] > 0
    assert "coefficients" in res
    assert len(res["chart_data"]) > 20
    assert res["next_forecast"]["point_forecast"] is not None


def test_methodology():
    """Verify methodology and academic references endpoint."""
    response = client.get("/api/methodology")
    assert response.status_code == 200
    data = response.json()
    assert "data_sources" in data
    assert "formulas" in data
    assert "academic_references" in data
