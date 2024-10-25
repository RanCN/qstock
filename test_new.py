from qstock import TurtleSystem

def back_test2(codes, index='sh', init_account_size=1000000.0, start='2022-01-01',end='2022-09-30'):
    sys = TurtleSystem(codes=codes, init_account_size=init_account_size, start=start,end=end)
    sys.back_test()
    
# back_test2(['鸿博股份', '高新发展'],'sh',1000000.0, '2023-03-03', '2023-09-05')
back_test2(['鸿博股份', '高新发展'],'sh',1000000.0, '2023-03-03', '2023-09-05')

