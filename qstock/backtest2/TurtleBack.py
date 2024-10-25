# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 21:18:13 2022

@author: Jinyi Zhang
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ..data.trade import get_data
from .BackBase import BackBase

def calcTR(high, low, close):
    '''Calculate True Range'''
    return np.max(np.abs([high-low, close-low, low-close]))


def getStratStats(log_returns: pd.Series,
                  risk_free_rate: float = 0.02):
    stats = {}  # Total Returns
    stats['tot_returns'] = np.exp(log_returns.sum()) - 1

    # Mean Annual Returns
    stats['annual_returns'] = np.exp(log_returns.mean() * 252) - 1

    # Annual Volatility
    stats['annual_volatility'] = log_returns.std() * np.sqrt(252)

    # Sortino Ratio
    annualized_downside = log_returns.loc[log_returns < 0].std() * \
        np.sqrt(252)
    stats['sortino_ratio'] = (stats['annual_returns'] -
                              risk_free_rate) / annualized_downside

    # Sharpe Ratio
    stats['sharpe_ratio'] = (stats['annual_returns'] -
                             risk_free_rate) / stats['annual_volatility']

    # Max Drawdown
    cum_returns = log_returns.cumsum() - 1
    peak = cum_returns.cummax()
    drawdown = peak - cum_returns
    max_idx = drawdown.argmax()
    stats['max_drawdown'] = 1 - np.exp(cum_returns[max_idx]) \
        / np.exp(peak[max_idx])

    # Max Drawdown Duration
    strat_dd = drawdown[drawdown == 0]
    strat_dd_diff = strat_dd.index[1:] - strat_dd.index[:-1]
    strat_dd_days = strat_dd_diff.map(lambda x: x.days).values
    strat_dd_days = np.hstack([strat_dd_days,
                               (drawdown.index[-1] - strat_dd.index[-1]).days])
    stats['max_drawdown_duration'] = strat_dd_days.max()
    return {k: np.round(v, 4) if type(v) == np.float_ else v
            for k, v in stats.items()}


class TurtleSystem(BackBase):
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
        if isinstance(codes, str):
            codes = [codes]
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

        self._prep_data()

    def _prep_data(self):
        self.data = self._get_data()
        self._calc_breakouts()
        self._calc_N()

    def _calc_breakouts(self):
        # Gets breakouts for all codes
        for t in self.codes:
            # Breakouts for enter long position (EL), exit long (ExL)
            # enter short (ES), exit short (ExS)
            self.data[t, 'S1_EL'] = self.data[t]['close'].rolling(
                self.sys1_entry).max()
            self.data[t, 'S1_ExL'] = self.data[t]['close'].rolling(
                self.sys1_exit).min()
            self.data[t, 'S2_EL'] = self.data[t]['close'].rolling(
                self.sys2_entry).max()
            self.data[t, 'S2_ExL'] = self.data[t]['close'].rolling(
                self.sys2_exit).min()

            if self.shorts:
                self.data[t, 'S1_ES'] = self.data[t]['close'].rolling(
                    self.sys1_entry).min()
                self.data[t, 'S1_ExS'] = self.data[t]['close'].rolling(
                    self.sys1_exit).max()
                self.data[t, 'S2_ES'] = self.data[t]['close'].rolling(
                    self.sys2_entry).min()
                self.data[t, 'S2_ExS'] = self.data[t]['close'].rolling(
                    self.sys2_exit).max()

    def _calc_N(self):
        # Calculates N for all codes
        for t in self.codes:
            tr = self.data[t].apply(
                lambda x: calcTR(x['high'], x['low'], x['close']), axis=1)
            self.data[t, 'N'] = tr.rolling(self.atr_periods).mean()

    def _check_cash_balance(self, shares, price):
        # Checks to see if we have enough cash to make purchase.
        # If not, resizes position to lowest feasible level
        if self.cash <= shares * price:
            shares = np.floor(self.cash / price)
        return shares

    def _adjust_risk_units(self, units):
        # Scales units down by 20% for every 10% of capital that has been lost
        # under default settings.
        cap_loss = 1 - self.portfolio_value / self.init_account_size
        if cap_loss > self.risk_reduction_level:
            scale = np.floor(cap_loss / self.risk_reduction_level)
            units *= (1 - scale * self.risk_reduction_rate)
        return units

    """
    计算所有持仓的收益，之后加上剩下的仓位
    """
    def _calc_portfolio_value(self, portfolio):
        values = [v1['value'] for v0 in portfolio.values() if type(v0) is dict
                  for k1, v1 in v0.items() if v1 is not None]
        pv = sum(values)

        pv += self.cash
        if np.isnan(pv):
            raise ValueError(f"PV = {pv}\n{portfolio}")
        return pv

    def _get_units(self, system):
        sys_all = self.sys1_allocation if system == 1 else self.sys2_allocation
        dollar_units = self.r_max * self.portfolio_value * sys_all
        print(dollar_units)
        dollar_units = self._adjust_risk_units(dollar_units)
        return dollar_units

    def _size_position(self, data, dollar_units):
        shares = np.floor(dollar_units / (
            self.risk_level * data['N'] * data['close']))
        return shares

    def _run_system(self, ticker, data, position, system=1):
        print(system, 'system')
        S = system  # System number
        price = data['close']
        if np.isnan(price):
            # Return current position in case of missing data
            return position
        N = data['N']
        dollar_units = self._get_units(S)
        shares = 0
        if position is None:
            if price == data[f'S{S}_EL']:  # Buy on breakout
                if S == 1 and self.last_s1_win[ticker]:
                    self.last_s1_win[ticker] = False
                    return None
                shares = self._size_position(data, dollar_units)
                print(shares, data, 'shares')
                stop_price = price - self.risk_level * N
                long = True
            elif self.shorts:
                if price == data[f'S{S}_ES']:  # Sell short
                    if S == 1 and self.last_s1_win[ticker]:
                        self.last_s1_win[ticker] = False
                        return None
                    shares = self._size_position(data, dollar_units)
                    stop_price = price + self.risk_level * N
                    long = False
            else:
                return None
            if shares == 0:
                return None
            # Ensure we have enough cash to trade
            shares = self._check_cash_balance(shares, price)
            value = price * shares

            self.cash -= value
            position = {'units': 1,
                        'shares': shares,
                        'entry_price': price,
                        'stop_price': stop_price,
                        'entry_N': N,
                        'value': value,
                        'long': long}
            if np.isnan(self.cash) or self.cash < 0:
                raise ValueError(
                    f"Cash Error\n{S}-{ticker}\n{data}\n{position}")

        else:
            if position['long']:
                # Check to exit existing long position
                if price == data[f'S{S}_ExL'] or price <= position['stop_price']:
                    self.cash += position['shares'] * price
                    if price >= position['entry_price']:
                        self.last_s1_win[ticker] = True
                    else:
                        self.last_s1_win[ticker] = False
                    position = None
                # Check to pyramid existing position
                elif position['units'] < self.unit_limit:
                    if price >= position['entry_price'] + position['entry_N']:
                        shares = self._size_position(data, dollar_units)
                        shares = self._check_cash_balance(shares, price)
                        self.cash -= shares * price
                        stop_price = price - self.risk_level * N
                        avg_price = (position['entry_price'] * position['shares'] +
                                     shares * price) / (position['shares'] + shares)
                        position['entry_price'] = avg_price
                        position['shares'] += shares
                        position['stop_price'] = stop_price
                        position['units'] += 1
            else:
                # Check to exit existing short position
                if price == data[f'S{S}_ExS'] or price >= position['stop_price']:
                    self.cash += position['shares'] * price
                    if S == 1:
                        if price <= position['entry_price']:
                            self.last_s1_win[ticker] = True
                        else:
                            self.last_s1_win[ticker] = False
                    position = None
                # Check to pyramid existing position
                elif position['units'] < self.unit_limit:
                    if price <= position['entry_price'] - position['entry_N']:
                        shares = self._size_position(data, dollar_units)
                        shares = self._check_cash_balance(shares, price)
                        self.cash -= shares * price
                        stop_price = price + self.risk_level * N
                        avg_price = (position['entry_price'] * position['shares'] +
                                     shares * price) / (position['shares'] + shares)
                        position['entry_price'] = avg_price
                        position['shares'] += shares
                        position['stop_price'] = stop_price
                        position['units'] += 1

            if position is not None:
                # Update value at each time step
                position['value'] = position['shares'] * price

        return position

    
    def back_test(self):
        self.run()
        port_values = self.get_portfolio_values()
        print(port_values)
        # 每日收益比
        returns = port_values / port_values.shift(1)
        log_returns = np.log(returns)
        cum_rets = log_returns.cumsum()
        print(cum_rets)
        index = 'sh'
        self.get_transactions()
        base = get_data(index,start=self.start, end=self.end)
        base['returns'] = base['close'] / base['close'].shift(1)
        base['log_returns'] = np.log(base['returns'])
        base['cum_rets'] = base['log_returns'].cumsum()
        # plt.figure(figsize=(15, 7))
        # plt.plot((np.exp(cum_rets) -1 )* 100, label='海龟交易策略')
        # plt.plot((np.exp(base['cum_rets']) - 1) * 100, label='基准指数')
        # plt.xlabel('Date')
        # plt.ylabel('Returns (%)')
        # plt.title('Cumulative Portfolio Returns')
        # plt.legend()
        # plt.tight_layout()
        # plt.show() 
