import backtrader as bt
import backtrader.indicators as ta

from ..model import Mutant

class MutantBabyBacktrader(bt.Strategy):
    def __init__(self, model=None, print_log=True):
        if model is not None:
            self.model = model
        else:
            self.model = Mutant()
        self.params = self.model.params
        self.data_close = self.datas[0].close
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
            "close": self.datas[0].close[0]
        }
        indicators = {
            "ema_1": self.ema_1[0],
            "ema_2": self.ema_2[0],
            "ema_3": self.ema_3[0],
            "macd": self.macd[0],
            "macd_signal": self.macd_signal[0],
            "macd_hist": self.macd_hist[0],
            #"macd_avg": self.macd_avg[0],
            "rsi": self.rsi[0]
        }
        if not self.position:
            order = self.model.get_order(candle, indicators)
            if order is not None:
                if order["trade_type"]=="Long":
                    self.log('BUY CREATE, %.2f' % self.data_close[0])
                    self.order = self.buy_bracket(exectype=bt.Order.Market,
                                                 limitprice=order["tp_price"],
                                                 stopprice=order["sl_price"])
                if order["trade_type"]=="Short":
                    self.log('SELL CREATE, %.2f' % self.data_close[0])
                    self.order = self.sell_bracket(exectype=bt.Order.Market,
                                                 limitprice=order["tp_price"],
                                                 stopprice=order["sl_price"])
        return None
                    
    def _generate_indicators(self):
        # EMA - Moving average exponential  
        self.ema_1 = ta.EMA(self.data_close, period=self.params["ema_1_length"][0])
        self.ema_2 = ta.EMA(self.data_close, period=self.params["ema_2_length"][0])
        self.ema_3 = ta.EMA(self.data_close, period=self.params["ema_3_length"][0])
        # MACD - Moving average convergence divergence
        macd = ta.MACD(
            period_me1=self.params["macd_fast_length"][0],
            period_me2=self.params["macd_slow_length"][0],
            period_signal=self.params["macd_signal_length"][0])
        self.macd = macd.macd
        self.macd_signal = macd.signal
        self.macd_hist = ta.MACDHisto(
            period_me1=self.params["macd_fast_length"][0],
            period_me2=self.params["macd_slow_length"][0],
            period_signal=self.params["macd_signal_length"][0])
        #self.macd_avg = ta.SMA(self.macd_hist, period=self.params["macd_average_length"][0])
        self.rsi = ta.RSI(self.data_close, period=self.params["rsi_length"][0], safediv=True)
        return None
