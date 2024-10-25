#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@File    ：__init__.py.py
@Author  ：Jinyi Zhang 
@Date    ：2022/9/29 20:21 
'''
#数据模块
#股票、债券、期货、基金等交易行情数据
from .trade import *

#新闻数据
from .news import *
#股票基本面数据
from .fundamental import *
##行业、概念板块数据
from .industry import *
#资金流向数据
from .money import *
#宏观经济数据
from .macro import *

#问财数据
from .wencai import *