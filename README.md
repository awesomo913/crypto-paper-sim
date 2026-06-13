# crypto-paper-sim

Paper-trading simulation utilities for comparing simple crypto strategies and running GoCryptoTrader (GCT) strategy configs.

> **Simulation only:** this repo is for paper/backtest/demo use only. It does **not** place live trades and should not be used with real funds.

## What this project contains

- Python scripts for paper simulations (offline historical data + live market-data paper loop).
- PowerShell runners for GoCryptoTrader backtester runs.
- `strategies/` exports (`.strat`) for GCT RSI and DCA strategy runs.

## Scripts

### `simulate_30d.py`
Runs a 30-candle paper comparison on bundled Binance daily candles:

- Aggressive RSI variant
- Long-term DCA variant

It expects GoCryptoTrader test data at `../gocryptotrader/testdata/binance_BTCUSDT_24h_2019_01_01_2020_01_01.csv`.

Run:

```bash
python simulate_30d.py
```

### `offline_aggressive_paper_demo.py`
Offline paper demo that mirrors the live RSI paper rules (`RSI(3)`, buy <= 47, sell >= 53) using bundled historical CSV data (no network).

Run:

```bash
python offline_aggressive_paper_demo.py
```

### `live_12h_paper_rsi_ccxt.py`
Live market-data paper loop (default 12h) using public Binance candles through `ccxt`.
No API keys are required.

Run (12h default):

```bash
python live_12h_paper_rsi_ccxt.py
```

Run a short probe (example: ~36 seconds):

```bash
PAPER_TEST_HOURS=0.01 python live_12h_paper_rsi_ccxt.py
```

## PowerShell runners (Windows)

### `run_gct_when_binance_works.ps1`
Runs two GoCryptoTrader backtests (30-day aggressive RSI and 30-day DCA) and writes reports.

Run (PowerShell):

```powershell
.\run_gct_when_binance_works.ps1
```

### `run_12h_gct_paper.ps1`
Starts a 12-hour GCT live-candle paper run (`real-orders=false`) and stops it automatically after 12 hours.

Run (PowerShell):

```powershell
.\run_12h_gct_paper.ps1
```

> These runner scripts currently contain a local `$base`/`$bt` path. Update that path to your own GoCryptoTrader `backtester` directory before running (for example: `$base = "c:/path/to/gocryptotrader/backtester"`).

## `strategies/` folder

The `strategies/` directory contains exported GoCryptoTrader strategy configuration files:

- `01-aggressive-rsi-5m-30d.strat` — RSI strategy config for aggressive 5m-style backtest setup.
- `02-longterm-dca-daily-30d.strat` — DCA strategy config for daily accumulation backtest setup.
- `03-live-aggressive-rsi-1m-paper.strat` — 1m RSI live-data **paper** config (`real-orders: false`).

These are config exports you can run with GCT backtester using `-singlerunstrategypath`.

## Prerequisites

- Python 3.10+
- `ccxt` (required for `live_12h_paper_rsi_ccxt.py`)
- GoCryptoTrader checkout if you want to use the bundled GCT CSV/testdata paths or PowerShell GCT runners

Install Python dependency:

```bash
pip install ccxt
```

## What this is NOT

- Not a live trading bot
- Not connected to real-funds order execution
- Not financial advice

Always validate strategy behavior in simulation/paper environments before making any real-world decisions.
