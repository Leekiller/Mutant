from copy import deepcopy
import talib as ta

class Mutant:
    """ Mutant is a trading strategy driven by indicators.

    """
    def __init__(self, **params):
        self.params = { # Default parameters
            "required_candles_length": 157,
            "tp": 0.6, # Unit of percentage
            "sl": 1.2, # Unit of percentage
            "ema_1_length": 126,
            "ema_2_length": 156,
            "ema_3_length": 121,
            "macd_fast_length": 45,
            "macd_slow_length": 54,
            "macd_signal_length": 45,
            "macd_average_length": 49,
            "rsi_length": 14,
            "rsi_long": 51,
            "rsi_short": 48
        }
        self.params.update(deepcopy(params))

    def get_order(self, candles):
        """ Take action based on the candles. 

        1. Calculate indicators with candles.
        2. Check the trend.
        3. Check if long/short condition is matched.
        4. Create order.

        Candles: A Pandas dataframe with required_caldles_length.
        Order:
            trade_type: Long/Short
            open_price: high/low of the current candle for long/short
            tp_price: take profit price 
            sl_price: stop loss price 

        To do:
            - Raise error if len(candles) < MINIMUM_CANDLES_LENGTH.
        """
        self._get_indicators(candles)
        trend = self._check_trend()
        if trend == "Bull" and self._is_long():
            order = self._generate_order("Long")
        elif trend == "Bear" and self._is_short():
            order = self._generate_order("Short")
        else:
            order = None
        return order

    def _get_indicators(self, candles):
        """ Get indicators from Pandas dataframe

        1. Convert Pandas dataframe to Numpy array.
        2. Extract latest candle.
        3. Calculate indicators.
        """
        open_hist = candles["open"].to_numpy()
        high_hist = candle["high"].to_numpy()
        low_hist = candle["low"].to_numpy()
        close_hist = candle["close"].to_numpy()
        volume_hist = candle["volume"].to_numpy()
        # Latest candle
        self.open = open_hist[-1]
        self.high = high_hist[-1]
        self.low = low_hist[-1]
        self.close = close_hist[-1]
        # TP/SL
        self.tp = self.params["tp"]
        self.sl = self.params["sl"]
        # EMA - Moving average exponential
        self.ema_1 = ta.EMA(close_hist, timeperiod=self.params["ema_1_length"])[-1]
        self.ema_2 = ta.EMA(close_hist, timeperiod=self.params["ema_2_length"])[-1]
        self.ema_3 = ta.EMA(close_hist, timeperiod=self.params["ema_3_length"])[-1]
        # MACD - Moving average convergence divergence
        self.macd, self.macd_signal, self.macd_hist = ta.MACD(
            close_hist, 
            fastperiod=self.params["macd_fast_length"],
            slowperiod=self.params["macd_slow_length"],
            signalperiod=self.params["macd_signal_length"]
        )
        # RSI - Relative strength index
        self.rsi = ta.RSI(close_hist, timeperiod=self.params["rsi_length"])
        self.rsi_long = self.params["rsi_long"]
        self.rsi_short = self.params["rsi_short"] 
        return None

    def _check_trend(self):
        if self.ema_2 > self.ema_3:
            trend = "Bull"
        elif self.ema_2 < self.ema_3:
            trend = "Bear"
        else:
            trend = "Neutral"
        return trend

    def _is_long(self):
        ema_1_long = self.ema_1 > self.low
        ema_2_long = self.ema_2 < self.close
        rsi_long = self.rsi > self.rsi_long
        macd_long = self.macd_hist < 0
        macd_avg_long = self.macd_avg > self.macd_hist
        if (ema_1_long 
                and ema_2_long
                and rsi_long
                and macd_long
                and macd_avg_long):
            return True
        else:
            return False

    def _is_short(self):
        ema_1_short = self.ema_1 < self.high
        ema_2_short = self.ema_2 > self.close
        rsi_short = self.rsi < self.rsi_short
        macd_short = self.macd_hist > 0
        macd_avg_short = self.macd_avg < self.macd_hist
        if (ema_1_short
                and ema_2_short
                and rsi_short
                and macd_short
                and macd_avg_short):
            return True
        else:
            return False

    def _generate_order(self, trade_type):
        if trade_type == "Long":
            order = {
                "trade_type": "Long",
                "open_price": self.high,
                "tp_price": self.high * (1 + self.tp/100),
                "sl_price": self.high * (1 - self.sl/100)
            }
        elif trade_type == "Short":
            order = {
                "trade_type": "Short",
                "open_price": self.low,
                "tp_price": self.low * (1 - self.tp/100),
                "sl_price": self.low * (1 + self.sl/100),
            }
        return order
