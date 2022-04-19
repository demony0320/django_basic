from UpbitHandler import UpbitHandler

import pprint
import pandas as pd
from datetime import datetime, timezone, timedelta

def test_current_price():
    upbit_handler= UpbitHandler()
    prices = upbit_handler.get_current_prices()
    up_price_df = pd.DataFrame(prices)
    up_price_df['pure_symbol'] = up_price_df['market'].str[4:]
    up_price_df = up_price_df.set_index('pure_symbol')
    print(len(up_price_df))
    assert len(up_price_df) == 1

def test_rsi():
    '''
        RSI osilliator is one of momemtu signal
        Avergae Ups/Average Downs   would be RS
        RSI = RS/1+RS
    '''
    upbit_handler= UpbitHandler()
    rsi = upbit_handler.get_current_rsi('KRW-BTC')
    print(" this through function : BTC rsi %f " % rsi)
    assert rsi > 0
    rsi = upbit_handler.get_current_rsi('KRW-ETH')
    print(" this through function : ETH rsi %f " % rsi)
    assert rsi > 0


def test_sharp_falling():
    ''' on 2021/12/04 there is massive & sharp falling BTC to 42k
    let's find out how could we buy on that kind of situtation
    '''
    upbit_handler= UpbitHandler()
    #dt=datetime(2021, 12, 4, 5, 30)
    dt=datetime(2021, 12, 4, 9, 0)
    candle_df = upbit_handler.get_candles(ticker='KRW-BTC', unit='minutes',min_unit=5,count=100,to=dt) 
    #let's test plot here
    import matplotlib.pyplot as plt
    plt.plot(candle_df['timestamp'], candle_df['trade_price'])
    plt.xlabel('timestamp (every 5min)')
    plt.ylabel('trace_price')
    plt.legend(['KRW-BTC'])
    plt.savefig('price_plot.png')

    pd.options.display.max_rows = 100
    pd.options.display.max_columns= 100
    #print(candle_df)
    min_change_idx = candle_df['change'].idxmin()
    min_price_idx = candle_df['low_price'].idxmin()
    print('minimum change first')
    #for target_idx in [min_change_idx, min_price_idx]:
    for target_idx in [min_price_idx]:
        if target_idx != 0 or target_idx != len(candle_df):
            #min_change = candle_df.iloc[target_idx-2:target_idx+3]
            target_candle= candle_df.iloc[min_price_idx]
            print(target_candle)
            print(  (target_candle['opening_price'] - target_candle['low_price']) / target_candle['opening_price']  * -1 * 100)
            #Lower than 5 %  with opening price, and it's never happened currently, we can buy. 
            #Need to figure out what else we need to check. 

            near_candle =  candle_df.iloc[target_idx-5:target_idx+6]
            m=near_candle['change'].lt(0)
            s=(~m).cumsum()[m]
            _df = near_candle[s.map(s.value_counts()).ge(5).reindex(near_candle.index,fill_value=False)]
            assert len(_df) == 6

def test_falling():
    upbit_handler= UpbitHandler()
    check_falling_result = upbit_handler.check_falling('KRW-BTC','minutes')
    assert check_falling_result == False

def test_get_market():
    upbit_handler= UpbitHandler()
    df = upbit_handler.get_all_market()
    print(df.market,type(df.market))
    assert ('KRW-ETH' in set(df.market))


'''
def test_find_change_all():
    upbit_handler= UpbitHandler()
    upbit_handler.find_change_all()
    # let check get_cnadles can fetch more than 2 market.
    '''
    

def test_stochastic():
    #just want to print something
    upbit_handler = UpbitHandler()
    upbit_handler.get_stochastic()
    assert (upbit_handler.k != 0 and upbit_handler.d != 0)


    
