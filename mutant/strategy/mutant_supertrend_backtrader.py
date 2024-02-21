import backtrader as bt
import backtrader.indicators as ta
from leekiller.backtrader_plugin.indicators import SuperTrend, TSV

import numpy as np

from ..model import MutantBaby

class MutantSupertrendBacktrader(bt.Strategy):
    def __init__(self, model=None, print_log=True):
        if model is not None:
            self.model = model
        else:
            self.model = MutantBaby()
        self.params = self.model.params
        self.data_close = self.datas[0].close
        self.volume = self.datas[0].volume
        self._generate_indicators()
        self.order = None
        self.print_log = print_log

    def log(self, txt, dt=None, do_print=False):
        if self.print_log or do_print:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))
        return None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return None
        elif order.status in [order.Completed]:
            # Check if an order has been completed
            # Attention: broker could reject order if not enough cash
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell(): 
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        # Write down: no pending order
        self.order = None
        return None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return None
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
        return None

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.data_close[0])
        candle = {
            "open": self.datas[0].open[0],
            "high": self.datas[0].high[0],
            "low": self.datas[0].low[0],
            "close": self.datas[0].close[0],
            "volume": self.datas[0].volume[0],
        }

        # stdir_main
        if self.stline_main[0] < self.data_close[0]:
            self.stdir_main = [-1]
        elif self.stline_main[0] > self.data_close[0]:
            self.stdir_main = [1]
        else: 
            self.stdir_main = [1]
        # stdir_prev_main
        if self.stline_main[-1] < self.data_close[-1]:
            self.stdir_prev_main = [-1]
        elif self.stline_main[-1] > self.data_close[-1]:
            self.stdir_prev_main = [1]
        else:
            self.stdir_prev_main = [1]
        # stdir_tf2
        if self.stline_tf2[0] < self.data_close[0]:
            self.stdir_tf2 = [-1]
        elif self.stline_tf2[0] > self.data_close[0]:
            self.stdir_tf2 = [1]
        else:
            self.stdir_tf2 = [1]
        
        indicators = {
            "ema": self.ema[0],
            "stline_main": self.stline_main[0],
            "stdir_main": self.stdir_main[0],
            "stdir_prev_main": self.stdir_prev_main[0],
            "stline_tf2": self.stline_tf2[0],
            "stdir_tf2": self.stdir_tf2[0],
            "tsv": self.tsv[0],
            "adx": self.adx[0]
        }

        long_open, long_close, short_open, short_close = self.model.get_order(candle, indicators)
        if not self.position:
            if long_open:
                self.log('Open Long, %.2f' % self.data_close[0])
                self.order = self.buy(exectype=bt.Order.Market)
            elif short_open:
                self.log('Open Short, %.2f' % self.data_close[0])
                self.order = self.sell(exectype=bt.Order.Market)
        elif short_close and self.position.size<0:
            if long_open:
                self.close()
                self.log('Open Long, %.2f' % self.data_close[0])
                self.order = self.buy(exectype=bt.Order.Market)
            else:
                self.close()
        elif long_close and self.position.size>0:
            if short_open:
                self.close()
                self.log('Open Short, %.2f' % self.data_close[0])
                self.order = self.sell(exectype=bt.Order.Market)
            else:
                self.close()
        return None
                    
    def _generate_indicators(self):
        # EMA - Moving average exponential  
        self.ema = ta.EMA(self.data_close, period=self.params["ema_length"][0])
        self.stline_main = SuperTrend(
            period=self.params["st_atr_main"][0], 
            multiplier=self.params["st_factor_main"])
        self.stline_tf2 = SuperTrend(
            period=self.params["st_atr_tf2"][0], 
            multiplier=self.params["st_factor_tf2"])
        self.tsv = TSV(
            tsv_length=self.params["tsv_length"][0],
            tsv_ma_length=self.params["tsv_ma_length"][0])
        self.adx = ta.ADX(period=self.params["adx_length"][0])
        return None
