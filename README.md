# Mutant

BTC trading strategies with optimized technical indicators, built on top of
[Backtrader](https://www.backtrader.com/) for backtesting and parameter
optimization.

Mutant separates the **trading logic** (pure, framework-agnostic decision
models) from the **execution layer** (Backtrader strategies). This makes the
signal logic easy to test, reuse, and optimize independently of the
backtesting engine.

## Features

- Pluggable signal **models** that turn a candle plus a set of indicators into
  trade decisions.
- Backtrader **strategy** wrappers that compute indicators, feed them to a
  model, and place orders.
- Example notebooks/scripts for **backtesting** and **parameter optimization**
  (via Differential Evolution).

## Project structure

```
Mutant/
├── mutant/
│   ├── model/                      # Pure trading-decision models (no Backtrader dependency)
│   │   ├── mutant_baby.py          # EMA + MACD + RSI momentum strategy
│   │   ├── mutant_supertrend.py    # EMA + Supertrend + TSV + ADX strategy
│   │   └── mutant_pair_btceth.py   # BTC/ETH pair strategy (placeholder)
│   └── strategy/                   # Backtrader strategy wrappers
│       ├── mutant_baby_backtrader.py
│       └── mutant_supertrend_backtrader.py
├── expt_notebooks/                 # Backtesting & optimization notebooks/scripts
├── setup.py
├── LICENSE                         # Apache License 2.0
└── README.md
```

## Architecture

The codebase is organized in two layers:

### `mutant.model` — decision logic

A model is a plain Python class with a `get_order(candle, indicators)` method.
It receives the current OHLC(V) candle and a dictionary of pre-computed
indicator values, and returns the trade decision. Models hold their tunable
parameters in `self.params` and expose `update_params()` so an optimizer can
sweep them.

- **`MutantBaby`** — a momentum strategy using three EMAs (trend filter), MACD
  histogram, and RSI. Returns an order dict with `trade_type`, `open_price`,
  `tp_price` (take profit) and `sl_price` (stop loss).
- **`MutantSupertrend`** — uses an EMA trend filter, a main and a secondary
  Supertrend, TSV (Time Segmented Volume), and ADX to emit long/short
  open/close signals.
- **`MutantPairBtcEth`** — placeholder for a BTC/ETH pair-trading model.

### `mutant.strategy` — Backtrader execution

Each strategy subclasses `backtrader.Strategy`. On `__init__` it builds the
required indicators; on every `next()` bar it assembles the `candle` and
`indicators` dicts, asks the model for a decision, and places the
corresponding bracket/market orders. The default model is instantiated if none
is supplied, so a strategy can be run with optimized or default parameters.

The Supertrend strategy depends on extra indicators (`SuperTrend`, `TSV`) from
the `leekiller.backtrader_plugin` package.

## Installation

```bash
git clone <repo-url>
cd Mutant
pip install -e .
```

This installs the `mutant` package (version `23.08`). You also need the
runtime dependencies used by the strategies and notebooks:

- `backtrader`
- `pandas`, `numpy`
- `matplotlib` (for plotting in the notebooks)
- `leekiller.backtrader_plugin` (provides the `SuperTrend` and `TSV` indicators)
- `leekiller.optimizer` (provides the `DE` Differential Evolution optimizer,
  used for parameter tuning)

> Note: market data is not included. Scripts expect CSV files under a `data/`
> directory (e.g. `data/BTCUSD_latest.csv`) with `open, high, low, close,
> volume` columns indexed by timestamp. The `data/` directory is gitignored.

## Usage

### Backtesting

A minimal backtest wires a model into its Backtrader strategy and runs it
through `cerebro`:

```python
import pandas as pd
import backtrader as bt

from mutant.model import MutantSupertrend
from mutant.strategy import MutantSupertrendBacktrader

# Load and resample data to 5-minute candles
dataframe = pd.read_csv("data/BTCUSD_latest.csv", parse_dates=True, index_col=0)
dataframe.index = pd.to_datetime(dataframe.index, format="ISO8601")
df = dataframe["2019-11-15":"2019-11-30"].groupby(pd.Grouper(freq="5Min")).agg({
    "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
})

model = MutantSupertrend()

cerebro = bt.Cerebro()
cerebro.adddata(bt.feeds.PandasData(dataname=df, datetime=None))
cerebro.addstrategy(MutantSupertrendBacktrader, model, print_log=True)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="mutant_trade")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="mutant_drawdown")
cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.0004)

results = cerebro.run()
print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
```

See `expt_notebooks/backtesting_mutant_supertrend.py` and the accompanying
notebooks for complete, runnable examples.

### Parameter optimization

`expt_notebooks/optimize_mutant_supertrend.py` shows how to subclass the `DE`
(Differential Evolution) optimizer from `leekiller.optimizer` to search the
model's parameter space, using averaged Sharpe ratio across randomly sampled
backtest windows as the objective:

```bash
cd expt_notebooks
python optimize_mutant_supertrend.py
```

## License

Licensed under the [Apache License 2.0](LICENSE).
