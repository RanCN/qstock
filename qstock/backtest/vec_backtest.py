# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 09:03:15 2022

@author: Jinyi Zhang
"""
import pandas as pd  
import numpy as np
import matplotlib.pyplot as plt
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False
from datetime import timedelta
#关掉pandas的warnings
pd.options.mode.chained_assignment = None
from qstock.data.trade import get_data

#获取数据
def data_feed(code,index='hs300',start='20000101',end='',fqt=2):
    #获取个股数据
    df=get_data(code,start=start,end=end,fqt=fqt).fillna(method='ffill')
    #指数数据,作为参照指标
    df['index']=get_data(index,start,end).close.pct_change().fillna(0)
    #计算收益率
    df['rets']=df.close.pct_change().fillna(0)
    #计算买入持有和对比指数的累计收益率
    df['rets_line']=(df.rets+1.0).cumprod()
    df['index_line']=(df['index']+1.0).cumprod()
    return df

#有交易策略时
def trade_indicators(df):
    if 'capital_ret' not in df.columns:
        return
    # 计算资金曲线
    df['capital'] = (df['capital_ret'] + 1).cumprod()
    df=df.reset_index()
    # 记录买入或者加仓时的日期和初始资产
    df.loc[df['position'] > df['position'].shift(1), 'start_date'] = df['date']
    df.loc[df['position'] > df['position'].shift(1), 'start_capital'] = df['capital'].shift(1)
    df.loc[df['position'] > df['position'].shift(1), 'start_stock'] = df['close'].shift(1)
    # 记录卖出时的日期和当天的资产
    df.loc[df['position'] < df['position'].shift(1), 'end_date'] = df['date']
    df.loc[df['position'] < df['position'].shift(1), 'end_capital'] = df['capital']
    df.loc[df['position'] < df['position'].shift(1), 'end_stock'] = df['close']
    # 将买卖当天的信息合并成一个dataframe
    df_temp = df[df['start_date'].notnull() | df['end_date'].notnull()]

    df_temp['end_date'] = df_temp['end_date'].shift(-1)
    df_temp['end_capital'] = df_temp['end_capital'].shift(-1)
    df_temp['end_stock'] = df_temp['end_stock'].shift(-1)

    # 构建账户交易情况dataframe：'hold_time'持有天数，
    #'trade_return'该次交易盈亏,'stock_return'同期股票涨跌幅
    trade = df_temp.loc[df_temp['end_date'].notnull(), ['start_date', 'start_capital', 'start_stock',
                                                       'end_date', 'end_capital', 'end_stock']]
    trade['hold_time'] = (trade['end_date'] - trade['start_date']).dt.days
    trade['trade_return'] = trade['end_capital'] / trade['start_capital'] - 1
    trade['stock_return'] = trade['end_stock'] / trade['start_stock'] - 1

    trade_num = len(trade)  # 计算交易次数
    max_holdtime = trade['hold_time'].max()  # 计算最长持有天数
    average_change = trade['trade_return'].mean()  # 计算每次平均涨幅
    max_gain = trade['trade_return'].max()  # 计算单笔最大盈利
    max_loss = trade['trade_return'].min()  # 计算单笔最大亏损
    total_years = (trade['end_date'].iloc[-1] - trade['start_date'].iloc[0]).days / 365
    trade_per_year = trade_num / total_years  # 计算年均买卖次数

    # 计算连续盈利亏损的次数
    trade.loc[trade['trade_return'] > 0, 'gain'] = 1
    trade.loc[trade['trade_return'] < 0, 'gain'] = 0
    trade['gain'].fillna(method='ffill', inplace=True)
    # 根据gain这一列计算连续盈利亏损的次数
    rtn_list = list(trade['gain'])
    successive_gain_list = []
    num = 1
    for i in range(len(rtn_list)):
        if i == 0:
            successive_gain_list.append(num)
        else:
            if (rtn_list[i] == rtn_list[i - 1] == 1) or (rtn_list[i] == rtn_list[i - 1] == 0):
                num += 1
            else:
                num = 1
            successive_gain_list.append(num)
    # 将计算结果赋给新的一列'successive_gain'
    trade['successive_gain'] = successive_gain_list
    # 分别在盈利和亏损的两个dataframe里按照'successive_gain'的值排序并取最大值
    max_successive_gain = trade[trade['gain'] == 1].sort_values(by='successive_gain', \
                        ascending=False)['successive_gain'].iloc[0]
    max_successive_loss = trade[trade['gain'] == 0].sort_values(by='successive_gain', \
                        ascending=False)['successive_gain'].iloc[0]
    
    #  输出账户交易各项指标
    print ('\n==============每笔交易收益率及同期股票涨跌幅===============')
    print (trade[['start_date', 'end_date', 'trade_return', 'stock_return']])
    print ('\n====================账户交易的各项指标=====================')
    print ('交易次数为：%d   最长持有天数为：%d' % (trade_num, max_holdtime))
    print ('每次平均涨幅为：%f' % average_change)
    print ('单次最大盈利为：%f  单次最大亏损为：%f' % (max_gain, max_loss))
    print ('年均买卖次数为：%f' % trade_per_year)
    print ('最大连续盈利次数为：%d  最大连续亏损次数为：%d' % (max_successive_gain, max_successive_loss))
    return trade

def trade_performance(df,plot=True):
    if 'capital_ret' in df.columns:
        df1 = df.loc[:,['index','rets', 'capital_ret']]
        name_dict={'index':'基准指数','rets':'买入持有','capital_ret':'交易策略'}
    else:
        df1 = df.loc[:,['index','rets']]
        name_dict={'index':'基准指数','rets':'买入持有'}
    #df1.loc[df.index[0], ['index','rets']] = 0

    #计算收益率
    #累计收益率
    acc_ret=(df1+1).cumprod()
    #计算总收益率
    total_ret=acc_ret.iloc[-1]-1
    #年化收益率，假设一年250个交易日
    annual_ret=pow(1+total_ret,250/len(df1))-1
    #最大回撤
    md=((acc_ret.cummax()-acc_ret)/acc_ret.cummax()).max()
    exReturn=df1-0.03/250
    #计算夏普比率
    sharper_atio=np.sqrt(len(exReturn))*exReturn.mean()/df1.std()
    #计算CAPM里的alpha和beta系数
    beta0=df1[['rets','index']].cov().iat[0,1]/df['index'].var()
    alpha0=(annual_ret['rets']-annual_ret['index']*beta0)
    if 'capital_ret' in df1.columns:
        beta1=df1[['capital_ret','index']].cov().iat[0,1]/df['index'].var()
        alpha1=(annual_ret['capital_ret']-annual_ret['index']*beta1)
        alpha=[np.nan,alpha0,alpha1,]
        beta=[np.nan,beta0,beta1,]
    else:
        alpha=[np.nan,alpha0]
        beta=[np.nan,beta0]
    # 计算每一年(月,周)股票,资金曲线的收益
    year_ret = df1.resample('A').apply(lambda x: (x + 1.0).prod() - 1.0)
    month_ret = df1.resample('M').apply(lambda x: (x + 1.0).prod() - 1.0)
    week_ret = df1.resample('W').apply(lambda x: (x + 1.0).prod() - 1.0)
    #去掉缺失值
    year_ret.fillna(0,inplace=True)
    month_ret.fillna(0,inplace=True)
    week_ret.fillna(0,inplace=True)
    #计算胜率
    year_win_rate = year_ret.apply(lambda s:len(s[s>0])/len(s[s!=0]))
    month_win_rate =month_ret.apply(lambda s:len(s[s>0])/len(s[s!=0]))
    week_win_rate = week_ret.apply(lambda s:len(s[s>0])/len(s[s!=0]))
    result=pd.DataFrame()
    result['总收益率']=total_ret
    result['年化收益率']=annual_ret
    result['最大回撤']=md
    result['夏普比率']=sharper_atio
    result['Alpha']=alpha
    result['Beta']=beta
    result['年胜率']=year_win_rate
    result['月胜率']=month_win_rate
    result['周胜率']=week_win_rate
    result=result.T.rename(columns=name_dict)
    if plot:
        acc_ret=acc_ret.rename(columns=name_dict)
        acc_ret.plot(figsize=(15,7))
        plt.title('策略累计净值',size=15)
        plt.xlabel('')
        ax=plt.gca()
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')
        plt.show()
    return result

def start_backtest(code,index='hs300',start='20000101',end='20220930',fqt=2,strategy=None):
    if not isinstance(code,str):
        trade_indicators(code.copy())
        return trade_performance(code.copy())
    print(f'回测标的：{code}')
    if end in ['',None]:
        end='至今'
    print(f'回测期间：{start}—{end}')
    d0=data_feed(code,index,start=start,end=end,fqt=fqt)
    if strategy is not None:
        df=strategy(d0)
        trade_indicators(df)
    else:
        df=d0
    return trade_performance(df)






