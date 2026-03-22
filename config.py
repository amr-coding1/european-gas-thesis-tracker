"""
Configuration for the European Gas Thesis Tracker
"""

import os

# === API Keys (env var override supported) ===
AGSI_API_KEY = os.environ.get("AGSI_API_KEY", "YOUR_API_KEY_HERE")  # Get free key at https://agsi.gie.eu

# === AGSI API ===
AGSI_BASE_URL = "https://agsi.gie.eu/api"
AGSI_HEADERS = {"x-key": AGSI_API_KEY}

# Countries to track (ISO 2-letter codes)
TRACKED_COUNTRIES = {
    "EU": {"name": "EU Aggregate", "param": {"type": "eu"}, "critical_threshold": 30},
    "NL": {"name": "Netherlands (TTF)", "param": {"country": "NL"}, "critical_threshold": 15},
    "DE": {"name": "Germany", "param": {"country": "DE"}, "critical_threshold": 25},
    "FR": {"name": "France", "param": {"country": "FR"}, "critical_threshold": 25},
    "IT": {"name": "Italy", "param": {"country": "IT"}, "critical_threshold": 30},
    "AT": {"name": "Austria", "param": {"country": "AT"}, "critical_threshold": 25},
    "BE": {"name": "Belgium", "param": {"country": "BE"}, "critical_threshold": 25},
}

# === Thesis Parameters ===
THESIS = {
    "name": "Long TTF Summer 2026 — Qatar LNG Supply Shock",
    "direction": "LONG",
    "instrument": "TTF Summer 2026 (Q3-26)",
    "entry_date": "2026-03-20",
    "timeframe": "3-6 months",
    "core_thesis": (
        "Iran's strike on Ras Laffan destroyed Trains 4 & 6, removing 12.8 mtpa of Qatari LNG "
        "for 3-5 years. European storage at ~29% entering injection season (April-October) with "
        "EU mandate to hit 90% by November 1. The Netherlands (where TTF is priced) at just 7.2%. "
        "Without Qatari LNG, Europe cannot fill storage — TTF must reprice higher to ration demand "
        "and attract marginal LNG cargoes from Asia."
    ),
    "bull_catalysts": [
        "Below-normal injection rates in April/May",
        "Asian LNG spot prices rising (cargo competition)",
        "Further Hormuz/Middle East escalation",
        "Hot European summer increasing cooling demand / gas burn",
        "EU reaffirming 90% storage mandate with no flexibility",
        "Additional LNG facility outages globally",
    ],
    "bear_risks": [
        "Sanctions relief / Russian gas resumption (Ukraine transit restart, LNG loophole enforcement dropped, TurkStream expansion) — political not physical, can reverse fast on a headline",
        "Ceasefire / rapid Ras Laffan repair timeline",
        "EU waiving or lowering storage mandate below 90%",
        "US LNG export surge filling the gap",
        "Mild summer reducing gas demand",
        "Demand destruction from high prices / recession",
        "Dark fleet Russian LNG already quietly backfilling more than market expects",
    ],
}

# === Scoring Weights ===
# Each indicator scores -2 (very bearish) to +2 (very bullish)
INDICATOR_WEIGHTS = {
    "storage_level": 2.0,       # Most important — core of thesis
    "storage_trajectory": 1.5,  # Is it filling/draining vs seasonal norm?
    "nl_storage": 1.5,          # Netherlands specifically (TTF pricing)
    "injection_rate": 1.5,      # Injection vs historical average
    "ttf_front_month": 1.0,     # Price confirming thesis direction
    "ttf_curve_shape": 1.0,     # Backwardation = bullish, contango = bearish
    "lng_disruption": 2.0,      # Qatar/Hormuz status
    "geopolitical": 1.0,        # Broader Middle East tensions
}

# === Data Paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HISTORICAL_CSV = os.path.join(DATA_DIR, "storage_history.csv")
THESIS_LOG = os.path.join(DATA_DIR, "thesis_scores.csv")
MANUAL_INPUTS_FILE = os.path.join(DATA_DIR, "manual_inputs.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# === Storage Mandate ===
STORAGE_MANDATE_PCT = 90
STORAGE_MANDATE_DEADLINE_MONTH = 11  # November
STORAGE_MANDATE_DEADLINE_DAY = 1
