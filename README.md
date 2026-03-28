# European Gas Thesis Tracker

A live, dynamically-updating trading thesis and monitoring system tracking the European natural gas supply crisis following the destruction of Qatar's Ras Laffan LNG infrastructure.

**Thesis:** Long TTF Summer 2026 — Iran's strikes on Ras Laffan destroyed 12.8 mtpa of Qatari LNG capacity for 3-5 years. European gas storage is critically low entering injection season. The refill maths simply do not work — TTF must reprice higher.

## What This Does

- Pulls **live European gas storage data** from the AGSI API (Gas Infrastructure Europe) for 7 countries
- Scores the thesis against **8 weighted bull/bear indicators** on a 0-100 scale
- Calculates the **refill maths** — required injection rate vs current rate at various EU mandate targets
- Tracks **Netherlands days-to-empty** (where TTF is priced)
- Generates **30-day storage trend charts** and country-by-country heatmaps
- Monitors a **6-position cross-asset portfolio** with live P&L, correlation analysis, and allocation tracking
- Fetches **live news headlines** from Google News RSS, grouped by thesis-relevant categories
- Includes a full **thought process and scenario analysis** section documenting the reasoning behind each position
- Runs as a **Jupyter notebook** (interactive, visual) or **CLI tool** (automated, scriptable)

## The Thesis

### Background

Europe imports the majority of its natural gas. After cutting Russian pipeline gas in 2022, Europe became heavily dependent on LNG — particularly from Qatar (the world's largest LNG exporter) and the US.

On 18-19 March 2026, Iranian missile strikes destroyed **Trains 4 and 6** at Qatar's Ras Laffan Industrial City — the single largest LNG complex on Earth. This removed **12.8 million tonnes per annum** of LNG capacity, roughly 17% of Qatar's output, for an estimated 3-5 years.

Simultaneously, Iran imposed a **selective blockade of the Strait of Hormuz**, further constraining all Gulf LNG exports to Western buyers.

### The Problem

EU gas storage sits at approximately **28.5%** capacity. The EU has a legal mandate to fill storage to at least 80-90% by December 1 (with flexibility down to 70%). Injection season — when Europe refills its underground storage — begins in April.

The maths:

| Target | TWh Needed | Required Injection (GWh/d) | Current Rate (GWh/d) | Gap |
|--------|-----------|---------------------------|---------------------|-----|
| 90% | ~700 | ~3,100 | ~980 | 3.2x |
| 80% | ~590 | ~2,600 | ~980 | 2.7x |
| 70% | ~470 | ~2,100 | ~980 | 2.2x |

Even at the loosest possible target, Europe needs to inject at **2-3x its current rate** for 7+ months. Without Qatari LNG, and with no substitute supplier large enough to fill the gap (Norway is maxed, Russia is banned by EU law, US LNG terminals are at capacity), the only mechanism to rebalance is **price** — TTF must rise until it attracts enough marginal LNG cargoes from Asia or destroys enough European demand.

### Bull Case

1. **Refill maths are broken** at every mandate level
2. **Netherlands (where TTF is priced) at ~7%** — roughly 30-40 days of storage remaining
3. **No swing supplier** — Norway maxed, Russia banned, US at capacity, Qatar destroyed/blocked
4. **EU banned Russian gas permanently** (January 2026 regulation) — the #1 bear risk is now legislation
5. **Asia competing for same LNG cargoes** — Qatar force majeure hit South Korea and China too
6. **Hormuz blockade** constrains even Qatar's remaining operational trains
7. **Theory of storage** — critically low inventories drive convenience yield spike and backwardation

### Bear Case

1. **Ceasefire / Hormuz reopening** — US aerial campaign could succeed
2. **EU drops storage mandate** — already lowered recommendation to 80%, floor at 70%
3. **Demand destruction** — at EUR 80-100/MWh European industry shuts down, reducing demand
4. **US LNG capacity additions** — Golden Pass, Plaquemines ramping through 2026
5. **Mild summer** — less cooling demand = less gas burn = easier refill
6. **Russian LNG shadow flows** — dark fleet/STS transfers larger than reported

### The Portfolio

The thesis is expressed through a cross-asset portfolio, not just a single TTF position:

| Position | Direction | Entry | Target | Stop | Weight | Rationale |
|----------|-----------|-------|--------|------|--------|-----------|
| TTF Q3-26 | Long | EUR 59.34 | EUR 80 / 100 | EUR 45 | 30% | Core thesis — EU refill maths |
| Cheniere (LNG) | Long | $299 | $335 | $265 | 25% | US LNG producer; profits from HH-TTF spread |
| Venture Global (VG) | Long | $17.50 | $25 | $12 | 10% | Higher-beta LNG play; 30% spot exposure |
| Equinor (EQNR) | Long | $41 | $50 | $35 | 10% | Europe's top pipeline gas supplier; pure price play |
| Brent Crude (BZ=F) | Long | $112.50 | $130 | $95 | 10% | Hormuz closure; geopolitical risk premium |
| Henry Hub (NG=F) | Short | $2.94 | $2.20 | $3.50 | 5% | Hedge — US gas decoupled from global crisis |

10% held as cash reserve. All positions entered as paper trades on TradingView.

## Project Structure

```
thesis-tracker/
├── European_Gas_Thesis.ipynb   # Interactive notebook — the main deliverable
├── run_tracker.py              # CLI tool for automated monitoring
├── config.py                   # API keys, positions, thesis parameters, scoring weights
├── data_pipeline.py            # AGSI API client with retry/rate-limiting
├── thesis_scorer.py            # 8-indicator weighted scoring framework
├── news_fetcher.py             # Google News RSS fetcher for live headlines
├── requirements.txt            # Python dependencies
├── data/                       # Historical snapshots (gitignored)
│   ├── storage_history.csv
│   ├── thesis_scores.csv
│   └── manual_inputs.json
└── reports/                    # Saved daily reports (gitignored)
```

## Notebook Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | Live European Gas Storage | Current storage levels for 7 countries with weekly deltas |
| 2 | The Refill Maths | Required injection rates at 90/80/75/70% targets vs current pace |
| 3 | 30-Day EU Storage Trend | Line charts showing EU and NL storage trajectories |
| 4 | Thesis Health Score | 8-indicator weighted composite score (0-100) with breakdown |
| 5 | Supply Picture | Visual breakdown of European gas supply sources and the Qatar gap |
| 6 | Country-by-Country Heatmap | Storage levels with critical threshold markers |
| 7 | Paper Trade Tracker | Live TTF P&L from Yahoo Finance |
| 8 | Related Positions & Portfolio | Full 6-position portfolio with live P&L, correlation heatmap, allocation chart |
| 9 | Bull / Bear Catalyst Tracker | Status of each bull catalyst and bear risk |
| 10 | Thought Process & Scenario Analysis | Thesis narrative, key developments, 4 scenarios with probabilities, hedge logic |
| 11 | Trade Journal | Dated entries with storage levels, scores, and actions |
| 12 | Live News & Intelligence Feed | Google News RSS headlines grouped by category (last 48 hours) |
| 13 | Exit Criteria | Defined take-profit, stop-loss, and review triggers |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the notebook (interactive, visual)
jupyter notebook European_Gas_Thesis.ipynb
# Then: Kernel -> Restart & Run All

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

## Data Sources

- **AGSI Transparency Platform** (Gas Infrastructure Europe) — daily storage levels, published at 19:30 CET. API docs: [agsi.gie.eu](https://agsi.gie.eu)
- **Yahoo Finance** (via yfinance) — live prices for TTF, Cheniere, Venture Global, Equinor, Brent, Henry Hub
- **Google News RSS** — live headlines filtered by thesis-relevant search queries

## Author

**Abdulrahman Mustafa**
BEng Electrical & Electronic Engineering, University of Surrey
[GitHub](https://github.com/amr-coding1) | [LinkedIn](https://www.linkedin.com/in/abdulrahman-92a7392a0/)
