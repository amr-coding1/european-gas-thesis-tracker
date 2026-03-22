"""
Data pipeline — pulls live data from AGSI API and other sources.
Handles retries, rate limiting, and robust error handling.
"""

import requests
import pandas as pd
import json
import os
import logging
import time
from datetime import datetime, timedelta
from config import (
    AGSI_BASE_URL, AGSI_HEADERS, TRACKED_COUNTRIES,
    DATA_DIR, HISTORICAL_CSV
)

log = logging.getLogger(__name__)


# ─── Helpers ───────────────────────────────────────────────────

def safe_float(val) -> float | None:
    """Convert to float, handling None/empty/'-'."""
    if val is None or val == "" or val == "-":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_api_response(data) -> dict | None:
    """Normalize the various AGSI response shapes into a single dict."""
    if isinstance(data, list):
        return data[0] if len(data) > 0 else None
    if isinstance(data, dict):
        if "data" in data:
            entries = data["data"]
            if isinstance(entries, list):
                return entries[0] if len(entries) > 0 else None
            if isinstance(entries, dict):
                return entries
        # Some endpoints return the object directly
        if "full" in data or "gasInStorage" in data:
            return data
    return None


# ─── AGSI API ──────────────────────────────────────────────────

def fetch_agsi_country(country_code: str, date: str = None, retries: int = 2) -> dict | None:
    """
    Fetch storage data for a single country/aggregate from AGSI.
    Retries on timeout/5xx with backoff.
    """
    if country_code not in TRACKED_COUNTRIES:
        log.error(f"Unknown country code: {country_code}")
        return None

    params = dict(TRACKED_COUNTRIES[country_code]["param"])
    if date:
        params["date"] = date

    for attempt in range(retries + 1):
        try:
            resp = requests.get(
                AGSI_BASE_URL,
                headers=AGSI_HEADERS,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            result = _parse_api_response(data)
            if result is None:
                log.warning(f"{country_code}: API returned empty/unparseable response")
            return result

        except requests.exceptions.Timeout:
            if attempt < retries:
                wait = 2 ** attempt
                log.warning(f"{country_code}: Timeout, retrying in {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
            else:
                log.error(f"{country_code}: Timeout after {retries + 1} attempts")
                return None

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            if status in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** attempt
                log.warning(f"{country_code}: HTTP {status}, retrying in {wait}s")
                time.sleep(wait)
            else:
                log.error(f"{country_code}: HTTP error {status}: {e}")
                return None

        except requests.exceptions.RequestException as e:
            log.error(f"{country_code}: Request failed: {e}")
            return None

    return None


def _extract_storage_record(code: str, data: dict) -> dict:
    """Extract a standardized storage record from raw API data."""
    return {
        "name": TRACKED_COUNTRIES[code]["name"],
        "full_pct": safe_float(data.get("full")),
        "gas_in_storage_twh": safe_float(data.get("gasInStorage")),
        "working_volume_twh": safe_float(data.get("workingGasVolume")),
        "injection_gwh": safe_float(data.get("injection")),
        "withdrawal_gwh": safe_float(data.get("withdrawal")),
        "net_withdrawal_gwh": safe_float(data.get("netWithdrawal")),
        "gas_day": data.get("gasDayStart", "unknown"),
        "trend": safe_float(data.get("trend")),
    }


def fetch_all_storage(date: str = None) -> dict:
    """Fetch storage data for all tracked countries. Adds 0.5s delay between calls to be polite."""
    results = {}
    for i, code in enumerate(TRACKED_COUNTRIES):
        if i > 0:
            time.sleep(0.5)  # Rate limiting
        data = fetch_agsi_country(code, date)
        if data:
            results[code] = _extract_storage_record(code, data)
        else:
            log.warning(f"Skipping {code} — no data returned")
    return results


def fetch_previous_day_storage(country_code: str = "EU") -> dict | None:
    """Fetch yesterday's storage to calculate trajectory."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    data = fetch_agsi_country(country_code, yesterday)
    if data:
        return _extract_storage_record(country_code, data)
    # Try day before if yesterday not available yet
    day_before = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    data = fetch_agsi_country(country_code, day_before)
    if data:
        return _extract_storage_record(country_code, data)
    return None


def fetch_week_ago_storage(country_code: str = "EU") -> dict | None:
    """Fetch storage from 7 days ago for weekly trajectory."""
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    data = fetch_agsi_country(country_code, week_ago)
    if data:
        return _extract_storage_record(country_code, data)
    return None


def fetch_storage_range(country_code: str, days_back: int = 30) -> list[dict]:
    """Fetch historical storage data for trend analysis. Uses date range to minimize calls."""
    results = []
    today = datetime.now()
    for i in range(days_back):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        data = fetch_agsi_country(country_code, date)
        if data:
            results.append({
                "date": date,
                "full_pct": safe_float(data.get("full")),
                "gas_in_storage_twh": safe_float(data.get("gasInStorage")),
                "net_withdrawal_gwh": safe_float(data.get("netWithdrawal")),
                "injection_gwh": safe_float(data.get("injection")),
                "withdrawal_gwh": safe_float(data.get("withdrawal")),
            })
        time.sleep(0.3)  # Rate limiting
    return results


# ─── Persistence ───────────────────────────────────────────────

def save_snapshot(storage_data: dict) -> pd.DataFrame:
    """Append today's storage snapshot to historical CSV."""
    if not storage_data:
        return pd.DataFrame()

    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    for code, d in storage_data.items():
        rows.append({
            "timestamp": timestamp,
            "country": code,
            "name": d["name"],
            "full_pct": d.get("full_pct"),
            "gas_in_storage_twh": d.get("gas_in_storage_twh"),
            "working_volume_twh": d.get("working_volume_twh"),
            "injection_gwh": d.get("injection_gwh"),
            "withdrawal_gwh": d.get("withdrawal_gwh"),
            "net_withdrawal_gwh": d.get("net_withdrawal_gwh"),
            "gas_day": d.get("gas_day"),
        })

    df = pd.DataFrame(rows)
    try:
        if os.path.exists(HISTORICAL_CSV):
            existing = pd.read_csv(HISTORICAL_CSV)
            # Dedup: skip if we already have data for this gas_day
            new_gas_days = set(df["gas_day"].unique())
            existing_gas_days = set(existing["gas_day"].unique())
            if new_gas_days.issubset(existing_gas_days):
                log.info("Snapshot already exists for this gas day, skipping")
                return df
            df.to_csv(HISTORICAL_CSV, mode="a", header=False, index=False)
        else:
            df.to_csv(HISTORICAL_CSV, index=False)
    except OSError as e:
        log.error(f"Failed to save snapshot: {e}")
    return df


def load_history() -> pd.DataFrame:
    """Load historical storage data."""
    if os.path.exists(HISTORICAL_CSV):
        try:
            return pd.read_csv(HISTORICAL_CSV, parse_dates=["timestamp"])
        except Exception as e:
            log.error(f"Failed to load history: {e}")
    return pd.DataFrame()


def get_previous_score_from_history(country: str = "EU") -> float | None:
    """Get the previous day's storage % for a country from saved history."""
    df = load_history()
    if df.empty:
        return None
    country_data = df[df["country"] == country].drop_duplicates(subset=["gas_day"], keep="last")
    country_data = country_data.sort_values("timestamp", ascending=False)
    if len(country_data) < 2:
        return None
    return country_data.iloc[1].get("full_pct")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=== Fetching live AGSI data ===\n")
    data = fetch_all_storage()
    for code, info in data.items():
        pct = info.get("full_pct")
        name = info["name"]
        nw = info.get("net_withdrawal_gwh")
        pct_str = f"{pct:6.2f}%" if pct is not None else "  N/A "
        nw_str = f"{nw}" if nw is not None else "N/A"
        print(f"  {name:25s}  {pct_str}  (net withdrawal: {nw_str} GWh/d)")

    print("\nSaving snapshot...")
    save_snapshot(data)
    print("Done.")
