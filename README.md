# European Gas Thesis Tracker

A live, dynamically-updating trading thesis and monitoring system tracking the European natural gas supply crisis following the destruction of Qatar's Ras Laffan LNG infrastructure.

**Thesis:** Long TTF Summer 2026 — Iran's strikes on Ras Laffan destroyed 12.8 mtpa of Qatari LNG capacity for 3-5 years. European gas storage is critically low entering injection season. The refill math does not work — TTF must reprice higher.

## What This Does

- Pulls **live European gas storage data** from the AGSI API (Gas Infrastructure Europe) for 7 countries
- Scores the thesis against **8 weighted bull/bear indicators** on a 0-100 scale
- Calculates the **refill math** — required injection rate vs current rate at various EU mandate targets
- Tracks **Netherlands days-to-empty** (where TTF is priced)
- Generates **30-day storage trend charts** and country-by-country heatmaps
- Includes a **paper trade tracker** with live P&L from Yahoo Finance
- Runs as a **Jupyter notebook** (interactive, visual) or **CLI tool** (automated, scriptable)

## The Thesis

### Background

Europe imports the majority of its natural gas. After cutting Russian pipeline gas in 2022, Europe became heavily dependent on LNG — particularly from Qatar (the world's largest LNG exporter) and the US.

On 18-19 March 2026, Iranian missile strikes destroyed **Trains 4 and 6** at Qatar's Ras Laffan Industrial City — the single largest LNG complex on Earth. This removed **12.8 million tonnes per annum** of LNG capacity, approximately 17% of Qatar's output, for an estimated 3-5 years.

Simultaneously, Iran imposed a **selective blockade of the Strait of Hormuz**, further constraining all Gulf LNG exports to Western buyers.

### The Problem

EU gas storage sits at approximately **28.5%** capacity. The EU has a legal mandate to fill storage to at least 80-90% by December 1 (with flexibility down to 70%). Injection season — when Europe refills its underground storage — starts in April.

The math:

| Target | TWh Needed | Required Injection (GWh/d) | Current Rate (GWh/d) | Gap |
|--------|-----------|---------------------------|---------------------|-----|
| 90% | ~700 | ~3,100 | ~980 | 3.2x |
| 80% | ~590 | ~2,600 | ~980 | 2.7x |
| 70% | ~470 | ~2,100 | ~980 | 2.2x |

Even at the loosest possible target, Europe needs to inject at **2-3x its current rate** for 7+ months. Without Qatari LNG, and with no substitute supplier large enough to fill the gap (Norway is maxed, Russia is banned by EU law, US LNG terminals are at capacity), the only mechanism to rebalance is **price** — TTF must rise until it attracts enough marginal LNG cargoes from Asia or destroys enough European demand.

### Bull Case

1. **Refill math is broken** at every mandate level
2. **Netherlands (where TTF is priced) at ~7%** — roughly 30-40 days of storage remaining
3. **No swing supplier** — Norway maxed, Russia banned, US at capacity, Qatar destroyed/blocked
4. **EU banned Russian gas permanently** (January 2026 regulation) — the #1 bear risk is now legislation
5. **Asia competing for same LNG cargoes** — Qatar force majeure hit South Korea and China too
6. **Hormuz blockade** constrains even Qatar's remaining operational trains
7. **Theory of storage** — critically low inventories drive convenience yield spike and backwardation

### Bear Case

1. **Ceasefire / Hormuz reopening** — US aerial campaign could succeed
2. **EU drops storage mandate** — already lowered recommendation to 80%, floor at 70%
3. **Demand destruction** — at €80-100/MWh European industry shuts down, reducing demand
4. **US LNG capacity additions** — Golden Pass, Plaquemines ramping through 2026
5. **Mild summer** — less cooling demand = less gas burn = easier refill
6. **Russian LNG shadow flows** — dark fleet/STS transfers larger than reported

### The Trade

- **Instrument:** TTF Natural Gas Futures, Q3-2026
- **Direction:** Long
- **Paper Trade Entry:** €59.34/MWh (22 March 2026)
- **Target 1:** €80/MWh (take half off)
- **Target 2:** €100/MWh (close remainder)
- **Stop Loss:** €45/MWh (pre-strike level — thesis is wrong)
- **Timeframe:** 3-6 months

## Project Structure

```
thesis-tracker/
├── European_Gas_Thesis.ipynb   # Interactive notebook — the main deliverable
├── run_tracker.py              # CLI tool for automated monitoring
├── config.py                   # API keys, country definitions, thesis parameters
├── data_pipeline.py            # AGSI API client with retry/rate-limiting
├── thesis_scorer.py            # 8-indicator weighted scoring framework
├── requirements.txt            # Python dependencies
├── data/                       # Historical snapshots (gitignored)
│   ├── storage_history.csv
│   ├── thesis_scores.csv
│   └── manual_inputs.json
└── reports/                    # Saved daily reports (gitignored)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the notebook (interactive, visual)
jupyter notebook European_Gas_Thesis.ipynb
# Then: Kernel → Restart & Run All

# Or run the CLI tracker
python3 run_tracker.py              # Single report
python3 run_tracker.py --save       # Save report to file
python3 run_tracker.py --json       # JSON output
python3 run_tracker.py --history 30 # 30-day EU storage history
python3 run_tracker.py --watch 120  # Live monitor, refresh every 2 hours

# Update manual inputs when news breaks
python3 run_tracker.py --update geo=escalation hormuz=closed ttf=2
```

## Scoring Framework

The thesis is scored on 8 weighted indicators, each ranging from -2 (very bearish) to +2 (very bullish):

| Indicator | Weight | What It Measures |
|-----------|--------|-----------------|
| EU Storage Level | 2.0x | Aggregate storage % vs historical norms |
| Storage Trajectory | 1.5x | Week-over-week change in storage |
| Netherlands (TTF) Storage | 1.5x | Storage at the TTF pricing location |
| Injection Rate | 1.5x | Current injection vs required pace for mandate |
| TTF Front-Month Price | 1.0x | Whether price is confirming thesis direction |
| TTF Curve Shape | 1.0x | Backwardation (bullish) vs contango (bearish) |
| LNG Supply Disruption | 2.0x | Qatar capacity offline + Hormuz status |
| Geopolitical Risk | 1.0x | Middle East escalation level |

Scores are normalised to 0-100 where 50 = neutral, 100 = max bullish, 0 = max bearish.

## Data Source

All storage data is sourced from the **AGSI Transparency Platform** operated by Gas Infrastructure Europe (GIE). Data represents status at 6AM CET, published daily at 19:30 CET with a second processing at 23:00 CET.

API documentation: [agsi.gie.eu](https://agsi.gie.eu)

## Author

**Abdulrahman Mustafa**
BEng Electrical & Electronic Engineering, University of Surrey
[GitHub](https://github.com/amr-coding1) | [LinkedIn](https://www.linkedin.com/in/abdulrahman-92a7392a0/)
