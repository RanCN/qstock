# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 17:39:06 2019

@author: Jinyi Zhang
"""

import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from qstock.data.money import stock_money

#正常显示画图时出现的中文和负号
from pylab import mpl
mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus']=False

#计算数据在系列时间周期内的收益率
def ret_date(data,w_list=[1,5,20,60,120]):
    df=pd.DataFrame()
    for w in w_list:
        df[str(w)+'日收益率%']=(((data/data.shift(w)-1)*100)
                            .round(2)
                            .iloc[w:]
                            .fillna(0)
                            .T
                            .iloc[:,-1])
    return df

#计算某期间动量排名
def ret_rank(data,w_list=[1,5,20,60,120],c=4):
    #c为w_list里第几个
    rets=ret_date(data,w_list)
    col=rets.columns[c]
    rank_ret=rets.sort_values(col,ascending=False)
    return rank_ret

#同花顺概念动量排名
def ret_top(ths_rets,n=10):
    ths_top=pd.DataFrame()
    for c in ths_rets.columns:
        ths_top[c]=ths_rets.sort_values(c,ascending=False)[:n].index
    return ths_top

#获取同花顺概念指数动量排名名称列表
def ret_top_list(ths_top):
    alist=ths_top.values.tolist()
    words=' '.join([' '.join(s) for s in alist])
    word_list=words.split(' ')
    w_set=set(word_list)
    w_data=[]
    for w in w_set:
       w_data.append([w,word_list.count(w)/len(word_list)])
    return w_data

