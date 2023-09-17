import qstock as qs
import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# df=qs.ths_pool('ljqs')

pro = ts.pro_api('1e4782bea79bcd044c3ba84497918e2da96895b81722f6cfddcc775b')

# print(df)
# df=qs.ret_rank(df)

# 查看前几行
# print(df.head())

# 分时
# df = qs.web_data('002069', '20230903', '20230904', '1')
# print(df)

# df = pro.daily(ts_code='002069.SZ', start_date='20230804', end_date='20230904')
# df.set_index('trade_date', inplace=True)
# df.index = pd.to_datetime(df.index, format='%Y%m%d')


# df = qs.get_data(['贵州茅台', '鸿博股份'], start='20230101')
# df.set_index([df.index,'name'],inplace=True)
# df=df.unstack()
# df.ffill(inplace=True)
# df=df.swaplevel(axis=1)
# print(df)


# qs.kline(df)

qs.back_test(['鸿博股份'],'sh',1000000.0, '2023-01-20', '2023-09-04')

data = [
    ['2023-04-01', 5],
    ['2023-04-02', 10],
    ['2023-04-03', 20],
    ['2023-04-04', 2.5],
]
df = pd.DataFrame(data, columns=['date', 'close'])
port_values = df['close']
returns = port_values / port_values.shift(1)
# print(df)
# print(returns)
# print(port_values.shift(1))

log_returns = np.log(returns)
cum_rets = log_returns.cumsum()


# print(returns)
# print(log_returns)
# print(cum_rets)

# print((np.exp(cum_rets) -1 )* 100)

# plt.figure(figsize=(15, 7))
# plt.plot((np.exp(cum_rets) -1 )* 100, label='海龟交易策略')
# plt.xlabel('Date')
# plt.ylabel('Returns (%)')
# plt.title('Cumulative Portfolio Returns')
# plt.legend()
# plt.tight_layout()
# plt.show() 

porperty = {'S1': {'鸿博股份': None}, 'S2': {'鸿博股份': None}, 'date': Timestamp('2023-06-20 00:00:00'), 'cash': 1006217.7199999997}