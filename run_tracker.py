#!/usr/bin/env python3
"""
European Gas Thesis Tracker — CLI Runner.

Pulls live AGSI data, scores the thesis against 8 indicators,
and generates a formatted report. Supports continuous monitoring,
historical lookback, and manual input updates.

Usage:
    python3 run_tracker.py                  # Full report to terminal
    python3 run_tracker.py --save           # Also save report to file
    python3 run_tracker.py --json           # JSON output for programmatic use
    python3 run_tracker.py --history 30     # Pull 30 days of EU storage history
    python3 run_tracker.py --watch          # Live monitor — refreshes every 2 hours
    python3 run_tracker.py --watch 30       # Live monitor — refreshes every 30 minutes
    python3 run_tracker.py --update geo=escalation ttf=2  # Update manual inputs
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime

from config import (
    THESIS, TRACKED_COUNTRIES, REPORTS_DIR, DATA_DIR,
    STORAGE_MANDATE_PCT, STORAGE_MANDATE_DEADLINE_MONTH, STORAGE_MANDATE_DEADLINE_DAY,
)
from data_pipeline import (
    fetch_all_storage, save_snapshot, fetch_storage_range,
    fetch_previous_day_storage, fetch_week_ago_storage,
)
from thesis_scorer import (
    score_storage_level, score_nl_storage, score_storage_trajectory,
    score_injection_rate, score_lng_disruption, score_geopolitical,
    compute_thesis_health, log_score, format_score_report,
    load_manual_inputs, save_manual_inputs, update_manual_input,
)

log = logging.getLogger(__name__)


# ─── Core Report Logic ─────────────────────────────────────────

def run_report(save_to_file: bool = False, output_json: bool = False, quiet: bool = False) -> dict | None:
    """Pull data, score thesis, generate report."""
    if not quiet:
        print("\n📡 Fetching live AGSI storage data...\n")

    storage_data = fetch_all_storage()
    if not storage_data:
        print("❌ Failed to fetch storage data. Check API key / connectivity.")
        return None

    # Save snapshot
    save_snapshot(storage_data)

    # Load manual inputs
    manual = load_manual_inputs()

    # Extract key values
    eu = storage_data.get("EU", {})
    nl = storage_data.get("NL", {})
    eu_pct = eu.get("full_pct")
    nl_pct = nl.get("full_pct")
    injection = eu.get("injection_gwh")
    month = datetime.now().month
    is_injection_season = 4 <= month <= 10

    # Fetch previous data for trajectory scoring
    if not quiet:
        print("  Fetching 7-day-ago data for trajectory...\n")
    prev_eu = fetch_week_ago_storage("EU")
    prev_nl = fetch_week_ago_storage("NL")

    prev_eu_pct = prev_eu.get("full_pct") if prev_eu else None

    # Score each indicator
    indicators = {
        "storage_level": score_storage_level(eu_pct),
        "storage_trajectory": score_storage_trajectory(eu_pct, prev_eu_pct, is_injection_season),
        "nl_storage": score_nl_storage(nl_pct),
        "injection_rate": score_injection_rate(injection, month),
        "ttf_front_month": int(manual.get("ttf_front_month_score", 0)),
        "ttf_curve_shape": int(manual.get("ttf_curve_shape_score", 0)),
        "lng_disruption": score_lng_disruption(
            float(manual.get("trains_offline_mtpa", 0)),
            bool(manual.get("hormuz_open", True))
        ),
        "geopolitical": score_geopolitical(str(manual.get("geopolitical", "stable"))),
    }

    # Compute health score
    result = compute_thesis_health(indicators)
    log_score(result)

    # JSON output mode
    if output_json:
        output = {
            "thesis": THESIS["name"],
            "score": result["score"],
            "signal": result["signal"],
            "storage": {
                code: {
                    "pct": d.get("full_pct"),
                    "gas_twh": d.get("gas_in_storage_twh"),
                    "net_withdrawal": d.get("net_withdrawal_gwh"),
                } for code, d in storage_data.items()
            },
            "indicators": indicators,
            "manual_inputs": manual,
            "timestamp": result["timestamp"],
        }
        print(json.dumps(output, indent=2))
        return result

    # Generate and print report
    report = format_score_report(result, storage_data, prev_eu, prev_nl)
    print(report)

    # ── Netherlands days-to-empty ──
    nl_gas = nl.get("gas_in_storage_twh")
    nl_nw = nl.get("net_withdrawal_gwh")
    if nl_pct is not None and nl_gas is not None and nl_nw is not None and nl_nw > 0:
        days_to_empty = (nl_gas * 1000) / nl_nw  # TWh → GWh
        print(f"\n  ⏱️  Netherlands days-to-empty at current rate: {days_to_empty:.0f} days")

    # ── Refill math ──
    if eu_pct is not None:
        gap = STORAGE_MANDATE_PCT - eu_pct
        if gap > 0:
            eu_cap = eu.get("working_volume_twh")
            if eu_cap and eu_cap > 0:
                twh_needed = (gap / 100) * eu_cap
                try:
                    deadline = datetime(
                        datetime.now().year,
                        STORAGE_MANDATE_DEADLINE_MONTH,
                        STORAGE_MANDATE_DEADLINE_DAY
                    )
                    days_to_deadline = (deadline - datetime.now()).days
                except ValueError:
                    days_to_deadline = 0

                if days_to_deadline > 0:
                    daily_needed = (twh_needed * 1000) / days_to_deadline  # GWh/d
                    print(f"  📊 EU needs to inject {twh_needed:.0f} TWh over {days_to_deadline} days to hit {STORAGE_MANDATE_PCT}%")
                    print(f"     Required avg injection: {daily_needed:.0f} GWh/d")
                    if injection is not None and injection > 0:
                        print(f"     Current injection rate: {injection:.0f} GWh/d")
                        ratio = daily_needed / injection
                        print(f"     Gap ratio: {ratio:.1f}x current rate needed")
                    elif injection is not None:
                        print(f"     Current injection rate: {injection:.0f} GWh/d (in net withdrawal)")
                elif days_to_deadline <= 0:
                    print(f"  📊 Storage mandate deadline has passed for this year")
        else:
            print(f"  ✅ EU storage above {STORAGE_MANDATE_PCT}% mandate — thesis weakening")

    print()

    # Save to file
    if save_to_file:
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = os.path.join(REPORTS_DIR, f"report_{date_str}.txt")
        try:
            with open(filepath, "w") as f:
                f.write(report)
            print(f"  💾 Report saved to {filepath}\n")
        except OSError as e:
            print(f"  ❌ Failed to save report: {e}\n")

    return result


# ─── Watch Mode (Live Monitor) ─────────────────────────────────

def run_watch(interval_minutes: int = 120):
    """
    Continuously monitor thesis health. Refreshes at given interval.
    Press Ctrl+C to stop.
    """
    running = True

    def _handle_sigint(sig, frame):
        nonlocal running
        running = False
        print("\n\n  🛑 Stopping watch mode...\n")

    signal.signal(signal.SIGINT, _handle_sigint)

    print(f"\n🔄 WATCH MODE — Refreshing every {interval_minutes} minutes. Press Ctrl+C to stop.\n")
    print("=" * 70)

    run_count = 0
    prev_score = None

    while running:
        run_count += 1
        print(f"\n  ── Run #{run_count} at {datetime.now().strftime('%H:%M:%S')} ──\n")

        result = run_report(save_to_file=True, quiet=True)

        if result:
            score = result["score"]
            # Alert on significant changes
            if prev_score is not None:
                delta = score - prev_score
                if abs(delta) >= 5:
                    print(f"\n  🚨 SCORE CHANGE: {prev_score} → {score} ({delta:+.1f})")
                    if delta > 0:
                        print(f"     Thesis STRENGTHENING")
                    else:
                        print(f"     Thesis WEAKENING")
            prev_score = score

        # Wait for next refresh
        if running:
            next_run = datetime.now().strftime('%H:%M')
            print(f"\n  ⏳ Next refresh in {interval_minutes} minutes...")
            for _ in range(interval_minutes * 60):
                if not running:
                    break
                time.sleep(1)

    print("  Watch mode stopped. All reports saved to /reports/\n")


# ─── History Mode ──────────────────────────────────────────────

def run_history(days: int = 30):
    """Pull historical storage data and display trend."""
    import pandas as pd

    print(f"\n📡 Fetching {days} days of EU storage history...\n")
    history = fetch_storage_range("EU", days)

    if not history:
        print("❌ No historical data retrieved.")
        return

    print(f"  {'Date':12s}  {'Storage %':>10s}  {'Net W/D (GWh/d)':>16s}  {'Inj (GWh/d)':>12s}")
    print(f"  {'─' * 12}  {'─' * 10}  {'─' * 16}  {'─' * 12}")

    sorted_history = sorted(history, key=lambda x: x["date"])
    prev_pct = None
    for entry in sorted_history:
        pct = entry.get("full_pct")
        nw = entry.get("net_withdrawal_gwh")
        inj = entry.get("injection_gwh")
        pct_str = f"{pct:.2f}%" if pct is not None else "N/A"
        nw_str = f"{nw:,.0f}" if nw is not None else "N/A"
        inj_str = f"{inj:,.0f}" if inj is not None else "N/A"

        # Show delta
        delta_str = ""
        if pct is not None and prev_pct is not None:
            delta = pct - prev_pct
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "─"
            delta_str = f"  {arrow} {delta:+.2f}pp"
        prev_pct = pct

        print(f"  {entry['date']:12s}  {pct_str:>10s}  {nw_str:>16s}  {inj_str:>12s}{delta_str}")

    # Save
    df = pd.DataFrame(sorted_history)
    path = os.path.join(DATA_DIR, "eu_history.csv")
    df.to_csv(path, index=False)
    print(f"\n  💾 History saved to {path}")


# ─── Manual Input Updates ──────────────────────────────────────

def handle_updates(updates: list[str]):
    """
    Parse and apply manual input updates.
    Format: key=value
    Shortcuts:
        geo=escalation    → geopolitical=escalation
        ttf=2             → ttf_front_month_score=2
        curve=1           → ttf_curve_shape_score=1
        hormuz=closed     → hormuz_open=False
        trains=12.8       → trains_offline_mtpa=12.8
    """
    shortcuts = {
        "geo": "geopolitical",
        "ttf": "ttf_front_month_score",
        "curve": "ttf_curve_shape_score",
        "hormuz": "hormuz_open",
        "trains": "trains_offline_mtpa",
    }

    for update in updates:
        if "=" not in update:
            print(f"  ⚠️  Invalid format: '{update}' — use key=value")
            continue

        key, value = update.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Apply shortcuts
        key = shortcuts.get(key, key)

        # Type conversion
        if key == "hormuz_open":
            value = value.lower() not in ("false", "0", "closed", "no")
        elif key in ("trains_offline_mtpa",):
            try:
                value = float(value)
            except ValueError:
                print(f"  ⚠️  Invalid number for {key}: '{value}'")
                continue
        elif key in ("ttf_front_month_score", "ttf_curve_shape_score"):
            try:
                value = int(value)
                if not -2 <= value <= 2:
                    print(f"  ⚠️  {key} must be between -2 and 2")
                    continue
            except ValueError:
                print(f"  ⚠️  Invalid integer for {key}: '{value}'")
                continue

        update_manual_input(key, value)
        print(f"  ✅ {key} = {value}")

    # Show current state
    inputs = load_manual_inputs()
    print(f"\n  Current manual inputs:")
    for k, v in inputs.items():
        print(f"    {k}: {v}")


# ─── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="European Gas Thesis Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_tracker.py                    # Full report
  python3 run_tracker.py --watch            # Live monitor (2h refresh)
  python3 run_tracker.py --watch 30         # Live monitor (30min refresh)
  python3 run_tracker.py --history 30       # 30-day EU storage history
  python3 run_tracker.py --update geo=escalation ttf=2
  python3 run_tracker.py --update hormuz=closed
  python3 run_tracker.py --save --json      # Save + JSON output

Manual input shortcuts:
  geo     → geopolitical (de-escalation/ceasefire/stable/tensions/escalation)
  ttf     → ttf_front_month_score (-2 to +2)
  curve   → ttf_curve_shape_score (-2 to +2)
  hormuz  → hormuz_open (true/false/open/closed)
  trains  → trains_offline_mtpa (number)
        """,
    )
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--history", type=int, metavar="DAYS", help="Fetch N days of EU history")
    parser.add_argument("--watch", nargs="?", type=int, const=120, metavar="MINS",
                        help="Live monitor mode (default: 120 min refresh)")
    parser.add_argument("--update", nargs="+", metavar="KEY=VAL",
                        help="Update manual inputs (e.g., geo=escalation ttf=2)")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.update:
        handle_updates(args.update)
        print()
        # After updating, run a fresh report
        run_report(save_to_file=args.save, output_json=args.json)
    elif args.history:
        run_history(args.history)
    elif args.watch is not None:
        run_watch(interval_minutes=args.watch)
    else:
        run_report(save_to_file=args.save, output_json=args.json)


if __name__ == "__main__":
    main()
