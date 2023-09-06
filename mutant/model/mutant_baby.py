from copy import deepcopy

class MutantBaby:
    """ MutantBaby

    MutantBaby is a trading strategy based on several momentum indicators with optimized parameters. In this model we use
    EMA, MACD and RSI to determine the trades.
    """
    def __init__(self, **params):
        self.params = { 
            "tp": [0.6], # Unit of percentage
            "sl": [1.8], # Unit of percentage
            "ema_1_length": [126],
            "ema_2_length": [156],
            "ema_3_length": [121],
            "macd_fast_length": [45],
            "macd_slow_length": [54],
            "macd_signal_length": [45],
            #"macd_average_length": [49],
            "rsi_length": [14],
            "rsi_long": [51],
            "rsi_short": [48]
        }
        self.params.update(deepcopy(params))
        self.tp = self.params["tp"][0]
        self.sl = self.params["sl"][0]
        self.rsi_long = self.params["rsi_long"][0]
        self.rsi_short = self.params["rsi_short"][0]

    def update_params(self, params: dict=None):
        if params is not None:
            self.params = params
            self.tp = self.params["tp"][0]
            self.sl = self.params["sl"][0]
            self.rsi_long = self.params["rsi_long"][0]
            self.rsi_short = self.params["rsi_short"][0]
        return None

    def get_order(self, candle, indicators):
        """ Get order. 

        1. Check the trend.
        2. Check if long/short conditions are matched.
        3. Create order.

        Order:
            trade_type: Long/Short
            open_price: high/low of the current candle for long/short
            tp_price: take profit price 
            sl_price: stop loss price 
        """
        self.open = candle["open"]
        self.high = candle["high"]
        self.low = candle["low"]
        self.close = candle["close"]
        self.ema_1 = indicators["ema_1"]
        self.ema_2 = indicators["ema_2"]
        self.ema_3 = indicators["ema_3"]
        self.macd = indicators["macd"]
        self.macd_signal = indicators["macd_signal"]
        self.macd_hist = indicators["macd_hist"]
        #self.macd_avg = indicators["macd_avg"]
        self.rsi = indicators["rsi"]
        trend = self._check_trend()
        if trend == "Bull" and self._is_long():
            order = self._generate_order("Long")
        elif trend == "Bear" and self._is_short():
            order = self._generate_order("Short")
        else:
            order = None
        return order

    def _check_trend(self):
        if self.ema_2>self.ema_3 and self.ema_1>self.ema_3 and self.close>self.ema_3:
            trend = "Bull"
        elif self.ema_2<self.ema_3 and self.ema_1<self.ema_3 and self.close<self.ema_3:
            trend = "Bear"
        else:
            trend = "Neutral"
        return trend

    def _is_long(self):
        ema_long = self.ema_1 > self.ema_2
        rsi_long = self.rsi > self.rsi_long
        macd_long = self.macd_hist > 0
        if (ema_long and rsi_long and macd_long):
            return True
        else:
            return False

    def _is_short(self):
        ema_short = self.ema_1 < self.ema_2
        rsi_short = self.rsi < self.rsi_short
        macd_short = self.macd_hist < 0
        if (ema_short and rsi_short and macd_short):
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
