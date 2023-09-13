from copy import deepcopy
import numpy as np

class MutantSupertrend:
    """ MutantSupertrend

    MutantSupertrend is a trading strategy based on supertrend indicator. In this model we use
    EMA, Supertrend, TSV and ADX to determine the trades.
    """
    def __init__(self, **params):
        self.params = { 
            "ema_length": np.array([200]),
            "st_factor_main": np.array([16]),
            "st_atr_main": np.array([6]),
            "st_factor_tf2": np.array([3]),
            "st_atr_tf2": np.array([10]),
            "tsv_length": np.array([13]),
            "tsv_ma_length": np.array([7]),
            "adx_length": np.array([3]),
            "adx_threshold": np.array([60])
        }
        self.update_params(params)

    def update_params(self, params: dict=None):
        if params is not None:
            self.params.update(deepcopy(params))
        return None

    def get_order(self, candle, indicators):
        """ Get order. 

        Order:
            trade_type: Long/Short
        """
        self.open = candle["open"]
        self.high = candle["high"]
        self.low = candle["low"]
        self.close = candle["close"]
        self.ema = indicators["ema"]
        self.stline_main = indicators["stline_main"]
        self.stdir_main = indicators["stdir_main"]
        self.stdir_prev_main = indicators["stdir_prev_main"]
        self.stline_tf2 = indicators["stline_tf2"]
        self.stdir_tf2 = indicators["stdir_tf2"]
        self.tsv = indicators["tsv"]
        self.adx = indicators["adx"]
        self.adx_threshold = self.params["adx_threshold"][0]

        self._trade()
        return self.long_open, self.long_close, self.short_open, self.short_close

    def _trade(self):
        self.long_open = False
        self.long_close = False
        self.short_open = False
        self.short_close = False

        ema_long = self.close > self.ema
        st_long = self.stdir_main<0 and self.stdir_prev_main>0
        st_tf2_long = self.stdir_tf2 < 0
        tsv_long = self.tsv > 0
        adx_long = self.adx > self.adx_threshold

        ema_short = self.close < self.ema
        st_short = self.stdir_main>0 and self.stdir_prev_main<0
        st_tf2_short = self.stdir_tf2 > 0
        tsv_short = self.tsv < 0
        adx_short = self.adx > self.adx_threshold

        if (ema_long 
                and st_long 
                and st_tf2_long 
                and tsv_long 
                and adx_long):
            self.long_open = True

        if (ema_short and st_short and tsv_short):
            self.long_close = True

        if (ema_short 
                and st_short 
                and st_tf2_short 
                and tsv_short 
                and adx_short):
            self.short_open = True

        if (ema_long and st_long and tsv_long):
            self.short_close = True
