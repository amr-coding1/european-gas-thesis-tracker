"""
Thesis Health Scorer for the European Gas Thesis Tracker.
Evaluates the bull/bear balance across 8 weighted indicators using
a combination of live AGSI data and manual inputs (geopolitical level,
TTF curve shape, etc.). Outputs a normalised 0-100 composite score.
"""

import csv
import json
import os
import logging
from datetime import datetime
from config import THESIS, INDICATOR_WEIGHTS, TRACKED_COUNTRIES, THESIS_LOG, MANUAL_INPUTS_FILE

log = logging.getLogger(__name__)


# ─── Manual Inputs Manager ─────────────────────────────────────

DEFAULT_MANUAL_INPUTS = {
    "trains_offline_mtpa": 12.8,    # Qatar Trains 4 & 6 — destroyed March 2026
    "hormuz_open": True,            # Strait of Hormuz — selective blockade since March 2026
    "geopolitical": "tensions",     # One of: de-escalation / ceasefire / stable / tensions / escalation
    "ttf_front_month_score": 1,     # -2 to +2 (manual — check ICE TTF or TradingView)
    "ttf_curve_shape_score": 1,     # -2 to +2 (backwardation = bull, contango = bear)
}


def load_manual_inputs() -> dict:
    """Load manual inputs from JSON file, falling back to defaults."""
    if os.path.exists(MANUAL_INPUTS_FILE):
        try:
            with open(MANUAL_INPUTS_FILE, "r") as f:
                saved = json.load(f)
            # Merge with defaults so new keys are always present
            merged = {**DEFAULT_MANUAL_INPUTS, **saved}
            return merged
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"Failed to load manual inputs: {e}, using defaults")
    return dict(DEFAULT_MANUAL_INPUTS)


def save_manual_inputs(inputs: dict):
    """Persist manual inputs to JSON file."""
    try:
        with open(MANUAL_INPUTS_FILE, "w") as f:
            json.dump(inputs, f, indent=2)
    except OSError as e:
        log.error(f"Failed to save manual inputs: {e}")


def update_manual_input(key: str, value):
    """Update a single manual input and save."""
    inputs = load_manual_inputs()
    if key not in inputs:
        log.warning(f"Unknown manual input key: {key}")
        return
    inputs[key] = value
    save_manual_inputs(inputs)
    log.info(f"Updated {key} = {value}")


# ─── Scoring Functions ──────────────────────────────────────────

def score_storage_level(eu_pct: float | None) -> int:
    """Score EU aggregate storage level. Lower = more bullish for long TTF."""
    if eu_pct is None:
        return 0
    if eu_pct < 25:
        return 2   # Extremely low — very bullish
    elif eu_pct < 35:
        return 1   # Below normal — bullish
    elif eu_pct < 50:
        return 0   # Neutral
    elif eu_pct < 65:
        return -1  # Comfortable — bearish
    else:
        return -2  # Well-stocked — very bearish


def score_nl_storage(nl_pct: float | None) -> int:
    """Score Netherlands storage specifically (TTF pricing location)."""
    if nl_pct is None:
        return 0
    if nl_pct < 10:
        return 2   # Critical — very bullish
    elif nl_pct < 20:
        return 1   # Low — bullish
    elif nl_pct < 40:
        return 0   # Neutral
    elif nl_pct < 60:
        return -1  # Comfortable
    else:
        return -2  # Full


def score_storage_trajectory(current_pct: float | None, prev_pct: float | None, is_injection_season: bool) -> int:
    """
    Score whether WEEKLY storage trajectory supports thesis.
    Uses week-over-week delta in percentage points.
    """
    if current_pct is None or prev_pct is None:
        return 0
    delta = current_pct - prev_pct  # positive = filling, negative = draining

    if is_injection_season:
        # During injection season (Apr-Oct), SLOW filling is bullish for long TTF
        if delta < 0:
            return 2   # Still draining during injection season — very bullish
        elif delta < 1.5:
            return 1   # Barely filling — bullish (need ~3pp/week to hit target)
        elif delta < 3.0:
            return 0   # Normal fill rate
        elif delta < 5.0:
            return -1  # Fast filling — bearish
        else:
            return -2  # Very fast fill — very bearish
    else:
        # During withdrawal season (Nov-Mar), FAST draining is bullish
        if delta < -3.0:
            return 2   # Rapid drain — very bullish
        elif delta < -1.5:
            return 1   # Normal drain — mildly bullish
        elif delta < 0:
            return 0   # Slow drain — neutral
        elif delta < 1.0:
            return -1  # Barely draining or flat in winter — bearish
        else:
            return -2  # Filling in winter — very bearish


def score_injection_rate(injection_gwh: float | None, month: int) -> int:
    """Score injection rate vs what's needed to hit 90% by November."""
    if injection_gwh is None:
        return 0
    # During withdrawal season, injection rate isn't meaningful for scoring
    if month < 4 or month > 10:
        return 0
    # Benchmark: need ~3,000-4,000 GWh/d average to fill from ~30% to 90%
    if injection_gwh < 2000:
        return 2   # Way behind pace — very bullish
    elif injection_gwh < 3000:
        return 1   # Below pace — bullish
    elif injection_gwh < 4000:
        return 0   # On pace — neutral
    elif injection_gwh < 5000:
        return -1  # Ahead of pace — bearish
    else:
        return -2  # Filling fast — very bearish


def score_lng_disruption(trains_offline_mtpa: float, hormuz_open: bool) -> int:
    """Score LNG supply disruption level."""
    score = 0
    if trains_offline_mtpa >= 10:
        score += 2
    elif trains_offline_mtpa >= 5:
        score += 1

    if not hormuz_open:
        score += 1  # Additional risk from shipping disruption

    return min(score, 2)  # Cap at +2


def score_geopolitical(escalation_level: str) -> int:
    """Score geopolitical risk. Manual input."""
    levels = {
        "de-escalation": -2,
        "ceasefire": -1,
        "stable": 0,
        "tensions": 1,
        "escalation": 2,
    }
    result = levels.get(escalation_level)
    if result is None:
        log.warning(f"Unknown geopolitical level '{escalation_level}', defaulting to 0. "
                    f"Valid: {list(levels.keys())}")
        return 0
    return result


# ─── Composite Scoring ──────────────────────────────────────────

def compute_thesis_health(indicators: dict) -> dict:
    """
    Compute weighted thesis health score.
    Returns a normalised score 0-100 where 50 = neutral, 100 = max bullish, 0 = max bearish.
    """
    weighted_sum = 0
    details = {}

    for key, weight in INDICATOR_WEIGHTS.items():
        raw = indicators.get(key, 0)
        # Clamp to [-2, 2]
        raw = max(-2, min(2, raw))
        weighted = raw * weight
        weighted_sum += weighted
        details[key] = {"raw": raw, "weight": weight, "weighted": round(weighted, 2)}

    # Normalise: max_possible is if every indicator scores +2
    max_possible = sum(w * 2 for w in INDICATOR_WEIGHTS.values())
    # Map weighted_sum from [-max_possible, +max_possible] to [0, 100]
    normalized = ((weighted_sum / max_possible) + 1) * 50
    normalized = max(0.0, min(100.0, normalized))

    # Determine signal
    if normalized >= 75:
        signal, emoji = "STRONG BULL", "🟢🟢"
    elif normalized >= 60:
        signal, emoji = "BULL", "🟢"
    elif normalized >= 45:
        signal, emoji = "NEUTRAL", "🟡"
    elif normalized >= 30:
        signal, emoji = "BEAR", "🔴"
    else:
        signal, emoji = "STRONG BEAR", "🔴🔴"

    return {
        "score": round(normalized, 1),
        "signal": signal,
        "emoji": emoji,
        "weighted_sum": round(weighted_sum, 2),
        "max_possible": max_possible,
        "details": details,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def log_score(result: dict):
    """Append score to thesis log CSV."""
    try:
        file_exists = os.path.exists(THESIS_LOG)
        with open(THESIS_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "score", "signal", "weighted_sum"])
            writer.writerow([
                result["timestamp"],
                result["score"],
                result["signal"],
                result["weighted_sum"],
            ])
    except OSError as e:
        log.error(f"Failed to log score: {e}")


# ─── Report Formatting ─────────────────────────────────────────

def format_score_report(result: dict, storage_data: dict = None, prev_eu: dict = None, prev_nl: dict = None) -> str:
    """Format a human-readable thesis health report."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  THESIS HEALTH REPORT — {result['timestamp']}")
    lines.append(f"  {THESIS['name']}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  OVERALL SCORE:  {result['score']}/100  {result['emoji']}  {result['signal']}")
    lines.append(f"  Direction: {THESIS['direction']} {THESIS['instrument']}")
    lines.append("")

    # Storage snapshot
    if storage_data:
        lines.append("  ── LIVE STORAGE ──")
        for code, d in storage_data.items():
            pct = d.get("full_pct")
            threshold = TRACKED_COUNTRIES.get(code, {}).get("critical_threshold", 0)
            flag = " ⚠️  CRITICAL" if pct is not None and pct < threshold else ""
            name = d["name"]
            pct_str = f"{pct:.2f}%" if pct is not None else "N/A"
            nw = d.get("net_withdrawal_gwh")
            nw_str = f"(net w/d: {nw:+.0f} GWh/d)" if nw is not None else ""
            lines.append(f"    {name:25s}  {pct_str:>8s}  {nw_str}{flag}")
        lines.append("")

    # Week-over-week changes
    if prev_eu or prev_nl:
        lines.append("  ── WEEKLY CHANGE ──")
        if prev_eu and storage_data.get("EU"):
            cur = storage_data["EU"].get("full_pct")
            prev = prev_eu.get("full_pct")
            if cur is not None and prev is not None:
                delta = cur - prev
                arrow = "▲" if delta > 0 else "▼" if delta < 0 else "─"
                lines.append(f"    EU:          {prev:.2f}% → {cur:.2f}%  ({delta:+.2f}pp) {arrow}")
        if prev_nl and storage_data.get("NL"):
            cur = storage_data["NL"].get("full_pct")
            prev = prev_nl.get("full_pct")
            if cur is not None and prev is not None:
                delta = cur - prev
                arrow = "▲" if delta > 0 else "▼" if delta < 0 else "─"
                lines.append(f"    Netherlands: {prev:.2f}% → {cur:.2f}%  ({delta:+.2f}pp) {arrow}")
        lines.append("")

    # Indicator breakdown
    lines.append("  ── INDICATOR BREAKDOWN ──")
    labels = {
        "storage_level": "EU Storage Level",
        "storage_trajectory": "Storage Trajectory (7d)",
        "nl_storage": "Netherlands (TTF) Storage",
        "injection_rate": "Injection Rate vs Target",
        "ttf_front_month": "TTF Front-Month Price",
        "ttf_curve_shape": "TTF Curve Shape",
        "lng_disruption": "LNG Supply Disruption",
        "geopolitical": "Geopolitical Risk",
    }
    for key, detail in result["details"].items():
        raw = detail["raw"]
        bar_bull = "█" * max(0, raw) + "░" * (2 - max(0, raw))
        bar_bear = "█" * max(0, -raw) + "░" * (2 - max(0, -raw))
        if raw > 0:
            direction = f"BULL [{bar_bull}]"
        elif raw < 0:
            direction = f"BEAR [{bar_bear}]"
        else:
            direction = "NEUT [░░]"
        label = labels.get(key, key)
        lines.append(f"    {label:30s}  {raw:+d}  (x{detail['weight']:.1f})  {direction}")
    lines.append("")

    # Catalysts to watch
    lines.append("  ── BULL CATALYSTS ──")
    for c in THESIS["bull_catalysts"]:
        lines.append(f"    ◆ {c}")
    lines.append("")
    lines.append("  ── BEAR RISKS ──")
    for r in THESIS["bear_risks"]:
        lines.append(f"    ◇ {r}")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)
