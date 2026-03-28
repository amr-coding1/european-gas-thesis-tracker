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

# === Related Positions (Full Portfolio) ===
RELATED_POSITIONS = {
    "TTF": {
        "ticker": "TTF=F",
        "name": "TTF Natural Gas Q3-26",
        "direction": "LONG",
        "entry_price": 59.34,
        "entry_date": "2026-03-22",
        "target_1": 80.00,
        "target_2": 100.00,
        "stop_loss": 45.00,
        "weight": 0.30,
        "currency": "EUR",
        "unit": "/MWh",
        "category": "Gas/LNG",
    },
    "LNG": {
        "ticker": "LNG",
        "name": "Cheniere Energy",
        "direction": "LONG",
        "entry_price": 299.00,
        "entry_date": "2026-03-28",
        "target_1": 335.00,
        "target_2": None,
        "stop_loss": 265.00,
        "weight": 0.25,
        "currency": "USD",
        "unit": "",
        "category": "Equities",
    },
    "VG": {
        "ticker": "VG",
        "name": "Venture Global",
        "direction": "LONG",
        "entry_price": 17.50,
        "entry_date": "2026-03-28",
        "target_1": 25.00,
        "target_2": None,
        "stop_loss": 12.00,
        "weight": 0.10,
        "currency": "USD",
        "unit": "",
        "category": "Equities",
    },
    "EQNR": {
        "ticker": "EQNR",
        "name": "Equinor ASA",
        "direction": "LONG",
        "entry_price": 41.00,
        "entry_date": "2026-03-28",
        "target_1": 50.00,
        "target_2": None,
        "stop_loss": 35.00,
        "weight": 0.10,
        "currency": "USD",
        "unit": "",
        "category": "Equities",
    },
    "BRENT": {
        "ticker": "BZ=F",
        "name": "Brent Crude Oil",
        "direction": "LONG",
        "entry_price": 112.50,
        "entry_date": "2026-03-28",
        "target_1": 130.00,
        "target_2": None,
        "stop_loss": 95.00,
        "weight": 0.10,
        "currency": "USD",
        "unit": "/bbl",
        "category": "Oil",
    },
    "HH": {
        "ticker": "NG=F",
        "name": "Henry Hub Natural Gas",
        "direction": "SHORT",
        "entry_price": 2.94,
        "entry_date": "2026-03-28",
        "target_1": 2.20,
        "target_2": None,
        "stop_loss": 3.50,
        "weight": 0.05,
        "currency": "USD",
        "unit": "/MMBtu",
        "category": "Gas/LNG",
    },
}

UNALLOCATED_WEIGHT = 0.10  # Cash reserve

# === News Search Queries ===
NEWS_QUERIES = {
    "Gas/LNG": [
        "TTF gas price Europe",
        "Ras Laffan LNG Qatar",
        "European gas storage injection",
        "LNG cargo spot market",
        "Strait of Hormuz shipping",
    ],
    "Geopolitical": [
        "Iran war ceasefire negotiations",
        "Trump Iran deadline energy",
        "EU Russian gas ban sanctions",
        "Middle East escalation oil",
    ],
    "Equities": [
        "Cheniere Energy LNG stock",
        "Venture Global LNG",
        "Equinor gas production Norway",
    ],
    "Oil": [
        "Brent crude oil price Hormuz",
        "OPEC production supply",
    ],
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
