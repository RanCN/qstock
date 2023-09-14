import qstock as qs

# df=qs.ths_pool('ljqs')

# df = qs.realtime_change('快速反弹')
# print(df)
# df=qs.ret_rank(df)

#查看前几行
# print(df.head())

changes_list = ['火箭发射', '快速反弹', '加速下跌', '高台跳水', '大笔买入',
                '大笔卖出', '封涨停板', '封跌停板', '打开跌停板', '打开涨停板',
                '有大买盘', '有大卖盘', '竞价上涨', '竞价下跌', '高开5日线',
                '低开5日线', '向上缺口', '向下缺口', '60日新高', '60日新低',
                '60日大幅上涨', '60日大幅下跌']

n = range(1, len(changes_list) + 1)
change_dict = dict(zip(n, changes_list))

print(zip(n, changes_list), 'zip(n, changes_list)')

# 打印 changes_list 和 n
print("changes_list:", changes_list)
print("n:", list(n))

# 使用 zip 合并 n 和 changes_list
zipped = list(zip(n, changes_list))
print("zipped:", zipped)

# 使用 dict 创建一个字典
change_dict = dict(zipped)
print("change_dict:", change_dict)
