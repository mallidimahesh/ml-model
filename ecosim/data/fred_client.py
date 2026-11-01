"""FRED (Federal Reserve Economic Data) API Client for EcoSim.

Fetches US macroeconomic time-series data from the St. Louis Fed API.
Includes robust error handling, rate-limit safeguards, explicit demonstration mode,
and observation metadata tracking.
"""

from __future__ import annotations

import logging
from typing import Any
import requests
import pandas as pd

from ecosim.config import FRED_API_KEY, FRED_OBSERVATIONS_URL, FRED_SERIES
from ecosim.data.demo_data import generate_demo_macro_data

logger = logging.getLogger(__name__)


class FredClient:
    """Client for querying FRED API time series."""

    def __init__(self, api_key: str | None = None):
        """Initialize FRED client.

        Args:
            api_key: Optional explicit API key. If omitted, loads FRED_API_KEY from .env.
        """
        raw_key = api_key if api_key is not None else FRED_API_KEY
        self.api_key = str(raw_key).strip() if raw_key else ""
        self.is_live_configured = bool(
            self.api_key
            and self.api_key != "your_fred_api_key_here"
            and len(self.api_key) >= 16
        )

    def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[pd.DataFrame, bool, str | None]:
        """Fetch observations for a specific FRED series via the live API.

        Args:
            series_id: FRED Series identifier (e.g. 'GDPC1', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS', 'GS10').
            start_date: Optional observation start date 'YYYY-MM-DD'.
            end_date: Optional observation end date 'YYYY-MM-DD'.

        Returns:
            tuple: (DataFrame with ['date', 'value'], is_live_data, error_message_or_none)
        """
        if not self.is_live_configured:
            return (
                pd.DataFrame(columns=["date", "value"]),
                False,
                "FRED API key is not configured. Please add FRED_API_KEY to your .env file or enter it in settings.",
            )

        params: dict[str, Any] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        try:
            response = requests.get(FRED_OBSERVATIONS_URL, params=params, timeout=12)

            # Handle rate limiting
            if response.status_code == 429:
                err_msg = (
                    "FRED API rate limit reached (HTTP 429). The St. Louis Fed allows up to "
                    "120 requests per minute. Please pause briefly or switch to Demonstration Mode."
                )
                logger.warning(err_msg)
                return pd.DataFrame(columns=["date", "value"]), False, err_msg

            # Handle authorization or bad request errors
            if response.status_code in [400, 403]:
                try:
                    err_json = response.json()
                    detail = err_json.get("error_message", response.text[:120])
                except Exception:
                    detail = response.text[:120]
                err_msg = f"FRED API Authentication Error (HTTP {response.status_code}): {detail}"
                logger.warning(err_msg)
                return pd.DataFrame(columns=["date", "value"]), False, err_msg

            if response.status_code == 200:
                data = response.json()
                # Some error cases return 200 with an error_message key
                if "error_message" in data:
                    return (
                        pd.DataFrame(columns=["date", "value"]),
                        False,
                        f"FRED API Error: {data['error_message']}",
                    )

                observations = data.get("observations", [])
                if not observations:
                    return (
                        pd.DataFrame(columns=["date", "value"]),
                        True,
                        f"FRED returned zero observations for series {series_id} in the requested date range.",
                    )

                df = pd.DataFrame(observations)
                if "date" not in df.columns or "value" not in df.columns:
                    return (
                        pd.DataFrame(columns=["date", "value"]),
                        False,
                        f"Unexpected schema returned by FRED API for series {series_id}.",
                    )

                df = df[["date", "value"]].copy()
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                # FRED returns '.' for missing or holiday values
                df["value"] = pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce")
                df = df.dropna(subset=["date", "value"]).sort_values("date").reset_index(drop=True)

                if df.empty:
                    return (
                        pd.DataFrame(columns=["date", "value"]),
                        True,
                        f"All returned observations for {series_id} contained missing or unparseable values.",
                    )

                return df, True, None

            # Non-200 HTTP response
            err_msg = f"FRED API HTTP {response.status_code}: {response.text[:120]}"
            logger.warning(err_msg)
            return pd.DataFrame(columns=["date", "value"]), False, err_msg

        except requests.exceptions.Timeout:
            err_msg = "FRED API request timed out (12s limit). Check internet connectivity or switch to Demonstration Mode."
            logger.error(err_msg)
            return pd.DataFrame(columns=["date", "value"]), False, err_msg

        except Exception as exc:
            err_msg = f"Network connection error to FRED API: {exc}"
            logger.error(err_msg)
            return pd.DataFrame(columns=["date", "value"]), False, err_msg

    def fetch_demo_series(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Load the offline demonstration dataset containing historical US benchmarks (1990–2024).

        Returns:
            dict of {series_id: DataFrame}
        """
        demo_data = generate_demo_macro_data()
        filtered_demo: dict[str, pd.DataFrame] = {}

        for sid, df in demo_data.items():
            sub = df.copy()
            if start_date:
                sub = sub[sub["date"] >= pd.to_datetime(start_date)]
            if end_date:
                sub = sub[sub["date"] <= pd.to_datetime(end_date)]
            filtered_demo[sid] = sub.reset_index(drop=True)

        return filtered_demo

    def fetch_all_core_series(
        self,
        start_date: str | None = "1990-01-01",
        end_date: str | None = None,
        force_demo: bool = False,
    ) -> tuple[dict[str, pd.DataFrame], bool, list[str], dict[str, Any]]:
        """Fetch all 5 core macroeconomic series.

        Never silently mixes demonstration and live data. If live query is requested
        and any series fails or key is missing, reports the failure explicitly.

        Args:
            start_date: Earliest observation date (default: 1990-01-01).
            end_date: Latest observation date.
            force_demo: When True, bypasses API queries and explicitly loads demo data.

        Returns:
            tuple: (
                dict_of_dataframes,
                is_live_flag,
                list_of_messages,
                metadata_dict (latest dates, frequencies, counts)
            )
        """
        metadata: dict[str, Any] = {}

        # Path A: Explicit Demonstration Mode
        if force_demo or not self.is_live_configured:
            demo_dict = self.fetch_demo_series(start_date=start_date, end_date=end_date)
            for sid, df in demo_dict.items():
                if not df.empty:
                    meta_def = next((m for m in FRED_SERIES.values() if m["id"] == sid), None)
                    metadata[sid] = {
                        "latest_date": df["date"].iloc[-1],
                        "earliest_date": df["date"].iloc[0],
                        "count": len(df),
                        "frequency": meta_def["frequency"] if meta_def else "Monthly",
                        "units": meta_def["units"] if meta_def else "",
                        "name": meta_def["name"] if meta_def else sid,
                    }
            msg = (
                "Demonstration dataset active (historical US benchmarks 1990–2024). "
                "No live API requests made."
            )
            return demo_dict, False, [msg], metadata

        # Path B: Live FRED API queries
        live_results: dict[str, pd.DataFrame] = {}
        error_messages: list[str] = []

        for key, meta_def in FRED_SERIES.items():
            sid = meta_def["id"]
            df, is_live, err_msg = self.fetch_series(sid, start_date=start_date, end_date=end_date)

            if not is_live or df.empty:
                error_messages.append(f"{sid} ({meta_def['name']}): {err_msg or 'Empty observations'}")
            else:
                live_results[sid] = df
                metadata[sid] = {
                    "latest_date": df["date"].iloc[-1],
                    "earliest_date": df["date"].iloc[0],
                    "count": len(df),
                    "frequency": meta_def["frequency"],
                    "units": meta_def["units"],
                    "name": meta_def["name"],
                }

        # If any of the 5 series failed to load live, do NOT mix with demo data!
        if len(live_results) < len(FRED_SERIES):
            return {}, False, error_messages, {}

        return live_results, True, [], metadata
