import numpy as np
import qstock as qs
import json

sys_list = ['S1', 'S2']

# np.log('hello world')


class TurtleSystem:
    def __init__(self, codes, init_account_size=10000, risk_level=2, r_max=0.02,
               sys1_entry=20, sys1_exit=10, sys2_entry=55, sys2_exit=20,
               atr_periods=20, sys1_allocation=0.5, risk_reduction_rate=0.1,
               risk_reduction_level=0.2, unit_limit=5, pyramid_units=1, 
               start='2000-01-01', end='2020-12-31', shorts=True):

        self.codes = codes
        self.start = start
        self.end = end
        self.data = self._get_data()
        print(self.data)
        # print(enumerate(self.data.iterrows()))
        for i, (ts, row) in enumerate(self.data.iterrows()):
            print(row['鸿博股份']['code'])
            # print(ts, row)

    def _get_data(self):
        # Gets data for all codes
        df = qs.get_data(self.codes,start=self.start,end=self.end,fqt=2)
        df.set_index([df.index,'name'],inplace=True)
        df=df.unstack()
        df.ffill(inplace=True)
        df=df.swaplevel(axis=1)

        return df

# df = qs.get_data(self.codes,start=self.start,end=self.end,fqt=2)


codes = ['鸿博股份', '高新发展', '剑桥科技']
init_account_size = 1000000.0
start = '2023-08-29'
end = '2023-08-30'

sys = TurtleSystem(codes=codes, init_account_size=init_account_size, start=start,end=end)
