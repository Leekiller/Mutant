import backtrader as bt

from ..model import Mutant

class MutantBacktrader(bt.Strategy):
    def __init__(self):
        self.model = Mutant()
        self.params = self.model.params

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))
        return None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
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

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        pass

    def _generate_indicators(self):
        """ Get indicators from Pandas dataframe

        Candles are the data feed from Backtrader
        All the indicators are calculated using Backtrader.talib
        
        1. Extract latest candle.
        2. Calculate indicators.
        """
        close_hist = candles.close
        # Latest candle
        self.open = candles.open[0]
        self.high = candles.high[0]
        self.low = candles.low[0]
        self.close = candles.close[0]
        # EMA - Moving average exponential
        ema_1 = ta.EMA(close_hist, timeperiod=self.params["ema_1_length"])
        ema_2 = ta.EMA(close_hist, timeperiod=self.params["ema_2_length"])
        ema_3 = ta.EMA(close_hist, timeperiod=self.params["ema_3_length"])
        self.ema_1 = ema_1[0]
        self.ema_2 = ema_2[0]
        self.ema_3 = ema_3[0]
        # MACD - Moving average convergence divergence
        macd, macd_signal, macd_hist = ta.MACD(
            close_hist, 
            fastperiod=self.params["macd_fast_length"],
            slowperiod=self.params["macd_slow_length"],
            signalperiod=self.params["macd_signal_length"])
        self.macd = macd[0]
        self.macd_signal = macd_signal[0]
        self.macd_hist = macd_hist[0]
        # RSI - Relative strength index
        rsi = ta.RSI(close_hist, timeperiod=self.params["rsi_length"])
        self.rsi = rsi[0]
        return None

