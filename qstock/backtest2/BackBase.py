import numpy as np
import pandas as pd
from copy import deepcopy, copy
from qstock.data.trade import get_data

class BackBase:
    def __init__(self, codes, init_account_size=10000, risk_level=2, r_max=0.02,
               sys1_entry=20, sys1_exit=10, sys2_entry=55, sys2_exit=20,
               atr_periods=20, sys1_allocation=0.5, risk_reduction_rate=0.1,
               risk_reduction_level=0.2, unit_limit=5, pyramid_units=1, 
               start='2000-01-01', end='2020-12-31', shorts=True):
        '''
        :codes:股票代码或简称
        :init_account_size: int that sets initial trading capital
        :risk_level: float used to determine the stop loss distance by multiplying
        this value with N.
        :r_max: float max percentage of account that a trade can risk.
        :sys1_entry: int determines number of breakout days for System 1 to generate
        a buy signal.
        :sys1_exit: int determines number of breakout days for System 1 to generate
        a sell signal.
        :sys2_entry: int determines number of breakout days for System 2 to generate
        a buy signal.
        :sys2_exit: int determines number of breakout days for System 2 to generate
        a sell signal.
        :sys1_allocation: float to balance capital allocation 
        between System 1 and 2.
        :start: str first date for getting data.
        :end: str end date for getting data.
        :shorts: bool to allow short positions if True.
        :atr_periods: int number of days used to calculate SMA of N.
        :risk_reduction_rate: float < 1 represents the amount of loss the system
        sees before it reduces its trading size.
        :risk_reduction_level: float < 1 represents each increment in risk the
        the system reduces as it loses capital below its initial size.
        '''
        if isinstance(codes,str):
            codes=[codes]
        self.codes = codes
        self.init_account_size = init_account_size
        self.cash = init_account_size
        self.portfolio_value = init_account_size
        self.risk_level = risk_level
        self.r_max = r_max
        self.sys1_entry = sys1_entry
        self.sys1_exit = sys1_exit
        self.sys2_entry = sys2_entry
        self.sys2_exit = sys2_exit
        self.sys1_allocation = sys1_allocation
        self.sys2_allocation = 1 - sys1_allocation
        self.start = start
        self.end = end
        self.atr_periods = atr_periods
        self.shorts = shorts
        self.last_s1_win = {t: False for t in self.codes}
        self.unit_limit = unit_limit
        self.risk_reduction_level = risk_reduction_level
        self.risk_reduction_rate = risk_reduction_rate
        self.pyramid_units = pyramid_units
        self.sys_list = ['S1', 'S2']

    def _get_data(self):
        """
        将列数据，转化为每行以date为维度的数据，如
                    name    code    open    high     low   close  volume      turnover  turnover_rate
        date                                                                                         
        2023-08-29  剑桥科技  603083  101.98  105.65   99.59  105.10  276816  1.296997e+09          10.63
        2023-08-30  剑桥科技  603083  104.49  108.02  104.49  106.84  253649  1.223234e+09           9.74
        2023-08-29  鸿博股份  002229  181.74  194.14  178.88  191.14  899143  3.431788e+09          18.23
        2023-08-30  鸿博股份  002229  191.43  199.66  187.55  195.59  911834  3.600415e+09          18.49
        2023-08-29  高新发展  000628   44.24   47.55   43.96   47.27   68247  9.921511e+07           3.55
        2023-08-30  高新发展  000628   46.83   48.21   46.46   47.83   38778  5.827669e+07           2.02

        转化为

        name          剑桥科技    高新发展    鸿博股份    剑桥科技   高新发展    鸿博股份  ...          剑桥科技         高新发展          鸿博股份          剑桥科技          高新发展          鸿博股份
                    code    code    code    open   open    open  ...      turnover     turnover      turnover turnover_rate turnover_rate turnover_rate
        date                                                       ...                                                                                   
        2023-08-29  603083  000628  002229  101.98  44.24  181.74  ...  1.296997e+09  99215109.40  3.431788e+09         10.63          3.55         18.23
        2023-08-30  603083  000628  002229  104.49  46.83  191.43  ...  1.223234e+09  58276685.05  3.600415e+09          9.74          2.02         18.49
        """
        # Gets data for all codes
        df = get_data(self.codes,start=self.start,end=self.end,fqt=2)
        df.set_index([df.index,'name'],inplace=True)
        df=df.unstack()
        df.ffill(inplace=True)
        df=df.swaplevel(axis=1)
        return df
    
    def _run_system(self, code, data, position, system=1):
        return position
    
    def run(self):
        """
        运行函数，持仓初始化，遍历每天、每个codes、每个system，执行_run_system生成每天的position[system][code]数据
        """
        # Runs backtest on the turtle strategy
        self.portfolio = {}
        position = {s:
                    {code: None for code in self.codes}
                    for s in self.sys_list}

        for i, (ts, row) in enumerate(self.data.iterrows()):
            for code in self.codes:
                for s, system in enumerate(self.sys_list):
                    """
                    row[code]即该code该日期下的kline数据，position即该code该日期下的持仓数据
                    """
                    position[system][code] = self._run_system(
                        code, row[code], position[system][code], s + 1)
                    
            self.portfolio[i] = deepcopy(position)
            self.portfolio[i]['date'] = ts
            self.portfolio[i]['cash'] = copy(self.cash)
            self.portfolio_value = self._calc_portfolio_value(
                self.portfolio[i])
            
    def get_portfolio_values(self):
        vals = []
        for v in self.portfolio.values():
            pv = sum([v1['value'] for v0 in v.values() if type(v0) is dict
                      for k1, v1 in v0.items() if v1 is not None])
            pv += v['cash']
            vals.append(pv)
        return pd.Series(vals, index=self.data.index)
    
    def get_system_data_dict(self):
        sys_dict = {}
        cols = ['units', 'shares', 'entry_price', 'stop_price',
                'entry_N', 'value', 'long']
        X = np.empty(shape=(len(cols)))
        X[:] = np.nan
        index = [v['date'] for v in self.portfolio.values()]
        for s in self.sys_list:
            for t in self.codes:
                df = pd.DataFrame()
                for i, v in enumerate(self.portfolio.values()):
                    d = v[s][t]
                    if d is None:
                        if i == 0:
                            _array = X.copy()
                        else:
                            _array = np.vstack([_array, X])
                    else:
                        vals = np.array([float(d[i]) for i in cols])
                        if i == 0:
                            _array = vals.copy()
                        else:
                            _array = np.vstack([_array, vals])
                df = pd.DataFrame(_array, columns=cols, index=index)
                sys_dict[(s, t)] = df.copy()
        return sys_dict
    
    def get_transactions(self):
        ddict = self.get_system_data_dict()
        transactions = pd.DataFrame()
        for k, v in ddict.items():
            df = pd.concat([v, self.data[k[1]].copy()], axis=1)
            df.fillna(0, inplace=True)
            rets = df['close'] / df['entry_price'].shift(1) - 1
            trans = pd.DataFrame(rets[df['shares'].diff() < 0],
                                 columns=['Returns'])
            trans['System'] = k[0]
            trans['Ticker'] = k[1]
            trans['Long'] = df['long'].shift(1).loc[df['shares'].diff() < 0]
            trans['Units'] = df['units'].shift(1).loc[df['shares'].diff() < 0]
            trans['Entry_Price'] = df['entry_price'].shift(1).loc[
                df['shares'].diff() < 0]
            trans['Sell_Price'] = df['close'].loc[df['shares'].diff() < 0]
            trans['Shares'] = df['shares'].shift(
                1).loc[df['shares'].diff() < 0]
            trans.reset_index(inplace=True)
            trans.rename(columns={'index': 'Date'}, inplace=True)
            transactions = pd.concat([transactions, trans.copy()])

        transactions.reset_index(inplace=True)
        transactions.drop('index', axis=1, inplace=True)
        return transactions