import datetime
import sys

import pandas as pd
import numpy as np
import backtrader as bt
import backtrader.indicators as ta

from mutant.model import MutantSupertrend
from mutant.strategy import MutantSupertrendBacktrader
from leekiller.optimizer import DE

raw_data_path = "../data/BTCUSD_latest.csv"

class Optimizer(DE):
    def __init__(self):
        self.model = MutantSupertrend()
        self.control_params = self.model.params
        self.control_params_range = {
            'ema_length': np.array([5, 300]), 
            'st_factor_main': np.array([5, 30]), 
            'st_atr_main': np.array([5, 30]), 
            'st_factor_tf2': np.array([5, 60]), 
            'st_atr_tf2': np.array([5, 60]), 
            'tsv_length': np.array([5, 30]), 
            'tsv_ma_length': np.array([5, 30]), 
            'adx_length': np.array([2, 30]), 
            'adx_threshold': np.array([5, 90])
        }
        
        self.total_sessions = 2
        self.backtest_length = 1440*30 # Units of minute
        self.init_protfolio_value = 100000.0 # Units of USDT
        super().__init__()

    def load_data(self, data_path: str=None):
        if data_path is None:
            data_path = "../data/BTCUSD_latest.csv"
        dataframe = pd.read_csv(data_path, parse_dates=True, index_col=0)
        dataframe.index = pd.to_datetime(dataframe.index, format='ISO8601')
        self.dataframe = dataframe
        return None

    def get_objective_value(self, control_params: dict) -> tuple[float, dict]:
        """ Avraged ROI as objective value

        """
        self.model.update_params(control_params)
        trade_reports = []
        drawdown_reports = []
        sharp_reports = []
        sharp_ratio = []

        for i in range(self.total_sessions):
            start = np.random.choice(len(self.dataframe))
            while start > (len(self.dataframe) - self.backtest_length):
                start = np.random.choice(len(self.dataframe))
            end = start + self.backtest_length
            df = self.dataframe.iloc[start:end]
            df = df.groupby(pd.Grouper(freq='5Min')).agg({"open": "first", 
                                                          "high": "max",
                                                          "low": "min",
                                                          "close": "last",
                                                          "volume": "sum"})
            df = df.dropna()
            data = bt.feeds.PandasData(dataname=df,datetime=None)
            cerebro = bt.Cerebro()
            cerebro.addstrategy(MutantSupertrendBacktrader, self.model, print_log=False)
            cerebro.adddata(data)
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='mutant_trade')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mutant_drawdown')
            cerebro.addanalyzer(
                bt.analyzers.SharpeRatio,
                timeframe=bt.TimeFrame.Days,
                compression=1,
                factor=365,
                annualize =True,
                _name='mutant_sharpe')
            cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
            cerebro.broker.setcash(self.init_protfolio_value)
            cerebro.broker.setcommission(commission=0.0004)
            
            # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
            results = cerebro.run()
            result = results[0]
            # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
            # self.final_portfolio_value = cerebro.broker.getvalue()
            trade_reports.append(result.analyzers.mutant_trade.get_analysis())
            drawdown_reports.append(result.analyzers.mutant_drawdown.get_analysis())
            sharp_reports.append(result.analyzers.mutant_sharpe.get_analysis())

        info = self._get_info(trade_reports, drawdown_reports, sharp_reports)
        sharp_avg = info["Summary"]["sharp_avg"]
        return sharp_avg, info

    """ Trade report is provided by Backtrader.analyzers.TradeAnalyzer

    """
    def _get_info(self, trade_reports, drawdown_reports, sharp_reports) -> dict:
        info = {
            "Summary": {
                "total_sessions": self.total_sessions,
                "backtest_length": self.backtest_length,
                "num_trade_avg": 0,
                "roi_avg": 0,
                "winrate_avg": 0,
                "drawdown_avg": 0,
                "drawdown_max": 0,
                "sharp_avg": 0,
            },
            "num_trade": [0] * self.total_sessions,
            "roi": [0] * self.total_sessions,
            "winrate": [0] * self.total_sessions,
            "drawdown": [0] * self.total_sessions,
            "sharp": [0] * self.total_sessions
        }
        
        for i in range(self.total_sessions):
            trade_report = trade_reports[i]
            if trade_report['total']['total'] > 0:
                drawdown_report = drawdown_reports[i]
                sharp_report = sharp_reports[i]   
                info["num_trade"][i] = trade_report['total']['total']
                info["roi"][i] = self._get_roi(trade_report)
                info["winrate"][i] = self._get_winrate(trade_report)
                info["drawdown"][i] = -self._get_drawdown(drawdown_report)
                info["sharp"][i] = self._get_sharp(sharp_report)
        info["Summary"]["num_trade_avg"] = sum(info["num_trade"]) / len(info["num_trade"])
        info["Summary"]["roi_avg"] = sum(info["roi"]) / len(info["roi"])
        info["Summary"]["winrate_avg"] = sum(info["winrate"]) / len(info["winrate"])
        info["Summary"]["drawdown_avg"] = sum(info["drawdown"]) / len(info["drawdown"])
        info["Summary"]["drawdown_max"] = max(info["drawdown"])
        info["Summary"]["sharp_avg"] = sum(info["sharp"]) / len(info["sharp"])
        return info
    
    def _get_roi(self, trade_report):
        """ Get the ROI from trade report
    
        ROI = PNL / Initial Portfolio Value
        """
        pnl = trade_report.get('pnl', {}).get('net', {}).get('total', 0)
        roi = pnl / self.init_protfolio_value
        return roi

    def _get_winrate(self, trade_report):
        """ Get the win rate from trade report
        
        Win rate = number of win trades / number of total trades
        """
        total_trades = trade_report.get('total', {}).get('total', 0)
        win_trades = trade_report.get('won', {}).get('total', 0)
        win_rate = win_trades / total_trades
        return win_rate
    
    def _get_drawdown(self, drawdown_report):
        """ Get the drawdown from drawdown report
    
        """
        drawdown = drawdown_report.get('drawdown', 'nan')
        return drawdown

    def _get_sharp(self, sharp_report):
        sharp = sharp_report.get('sharperatio', 'nan')
        return sharp


def main():
    optimizer = Optimizer()
    optimizer.load_data()
    optimizer.run(itr=10, batch=2)
    pass


if __name__=="__main__":
    main()