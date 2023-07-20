from copy import deepcopy

class Mutant:
    """ Mutant is a trading strategy driven by indicators.

    """
    def __init__(self, **params):
        self.params = { # Default parameters
            "required_candles_length": 157,
            "tp": 0.6, # Unit of percentage
            "sl": 1.8, # Unit of percentage
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
        # TP/SL
        self.tp = self.params["tp"]
        self.sl = self.params["sl"]
        self.rsi_long = self.params["rsi_long"]
        self.rsi_short = self.params["rsi_short"] 

    def get_order(self, candle, indicators):
        """ Take action based on the candles. 

        1. Check the trend.
        2. Check if long/short condition is matched.
        3. Create order.

        Order:
            trade_type: Long/Short
            open_price: high/low of the current candle for long/short
            tp_price: take profit price 
            sl_price: stop loss price 

        To do:
            - Raise error if len(candles) < MINIMUM_CANDLES_LENGTH.
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
        self.macd_avg = indicators["macd_avg"]
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
