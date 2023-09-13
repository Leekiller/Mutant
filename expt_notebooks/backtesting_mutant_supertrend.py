# from __future__ import (absolute_import, division, print_function,
#                         unicode_literals)
import datetime
# import os.path
import sys

import pandas as pd
import numpy as np
import backtrader as bt
import backtrader.indicators as ta

import matplotlib
import tkinter
matplotlib.use('TKAgg')
# matplotlib.use('QT5Agg')

from mutant.model import MutantSupertrend
from mutant.strategy import MutantSupertrendBacktrader

raw_data_path = "../data/BTCUSD_latest.csv"
# raw_data_path = "../data/Raw_BTCUSDT1708-2303.csv"


dataframe = pd.read_csv(raw_data_path,
                                parse_dates=True,
                                index_col=0)
dataframe.index = pd.to_datetime(dataframe.index, format='ISO8601')
dataframe

start = "2019-11-15"
end = "2019-11-30"
df = dataframe[start:end]
df

model = MutantSupertrend()
print(model.params)

trade_reports = []
sharp_reports = []
drawdown_reports = []
total_sessions = 1
for i in range(total_sessions):
    # backtest_length = 1440
    # start = np.random.choice(len(dataframe) - backtest_length)
    # end = start + backtest_length
    # df = dataframe.iloc[start:end]
    df = dataframe[start:end]
    print(df)
    df = df.groupby(pd.Grouper(freq='5Min')).agg({"open": "first", 
                                                  "high": "max",
                                                  "low": "min",
                                                  "close": "last",
                                                  "volume": "sum"})
    data = bt.feeds.PandasData(dataname=df, datetime=None,)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MutantSupertrendBacktrader, model, print_log=True)
    cerebro.adddata(data)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='mutant_trade')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mutant_drawdown')
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        timeframe=bt.TimeFrame.Days, 
        compression=1, 
        factor=365,
        annualize =True,
        _name='mutant_sharpe'
    )
    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.0004)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    result = results[0]
    trade_reports.append(result.analyzers.mutant_trade.get_analysis())
    sharp_reports.append(result.analyzers.mutant_sharpe.get_analysis())
    drawdown_reports.append(result.analyzers.mutant_drawdown.get_analysis())
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())