import os
import jwt    # PyJWT 
import uuid
import hashlib
from urllib.parse import urlencode
import requests
import base64
import pprint
import pandas as pd 
import time
from datetime import datetime, timezone, timedelta
import json
from Tbot import Tbot

class UpbitHandler:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):         
            print("__new__ is called\n")
            cls._instance = super().__new__(cls)  
        return cls._instance                      

    def __init__(self):
        cls = type(self)
        if not hasattr(cls, "_init"):             
            print("__init__ is called\n")
            #self.data = data
            cls._init = True
            self.load_config()
            self.tbot = Tbot(self.telegram_token ,self.telegram_target)
    def load_config(self,full_path='./config.json'):
        f = open(full_path)
        self.config_json= json.load(f)
        self.server_url=self.config_json['server_url']
        self.telegram_token = self.config_json['telegram_token']
        self.telegram_target= self.config_json['telegram_target']

    def get_header(self,query=None):
        payload = {
            #'access_key': access_key,
            'access_key': self.config_json['access_key'],
            'nonce': str(uuid.uuid4()),
        }
        if query:
            payload['query'] = urlencode(query)
        #jwt_token = jwt.encode(payload, secret_key,algorithm='HS256').decode('utf-8')
        #jwt_token = jwt.encode(payload, self.config_json['secret_key'],algorithm='HS256').decode('utf-8')
        jwt_token = jwt.encode(payload, self.config_json['secret_key'],algorithm='HS256')
        auth_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": auth_token}
        return headers
    def check_account(self):
        res = requests.get(self.config_json['server_url']+ "/v1/accounts", headers=self.get_header() )
        return res.json()
    def check_profit(self):
        _account = self.check_account()
        df_account = pd.DataFrame(_account)
        df_account['avg_buy_price'] = pd.to_numeric(df_account['avg_buy_price'])
        df_account['balance'] = pd.to_numeric(df_account['balance'])
        df_account.set_index('currency', inplace=True)

        lst_symbol = [ 'KRW-' + x['currency'] for x in _account if x ]
        lst_symbol.remove('KRW-KRW')
        lst_symbol.remove('KRW-USDT')

        # get current prices through symbols
        _prices = self.get_current_prices(lst_symbol)
        df_prices = pd.DataFrame(_prices)
        df_prices['pure_symbol'] = df_prices['market'].str[4:]
        df_prices.set_index('pure_symbol',inplace=True)
        df_account['current_price'] = df_prices['trade_price']

        df_account ['profit'] = (df_account['current_price'] - df_account['avg_buy_price'] ) * df_account['balance']
        df_account ['profit_pct'] = (df_account['current_price'] - df_account['avg_buy_price'] ) / df_account['avg_buy_price'] * 100
        return df_account
        
        # ( Current prices -  current prices ) * balance  for each symbols


    def get_current_prices(self,symbols=['KRW-BTC']):
        #query= {"markets" : symbol}
        query= {"markets" : symbols }
        res = requests.get(self.server_url + "/v1/ticker", params=query, headers=self.get_header(query) )
        return res.json()
    def check_available_order(self,symbol='KRW-BTC'):
        query= {"market" : symbol}
        res = requests.get(self.server_url + "/v1/orders/chance", params=query, headers=self.get_header(query) )
        return res.json()
    def get_all_tickers(self,detail=False):
        #print("A") if a > b else print("B")
        if detail:
            detail_str = 'true'
        else:
            detail_str = 'false'
        query = { 'isDetails' : detail_str }
        res = requests.get(self.server_url + "/v1/market/all", params=query, headers=self.get_header(query) )
        return res.json()

    def get_kr_tickers(self,detail=False):
        #print("A") if a > b else print("B")
        if detail:
            detail_str = 'true'
        else:
            detail_str = 'false'
        query = { 'isDetails' : detail_str }
        res = requests.get(self.server_url + "/v1/market/all", params=query, headers=self.get_header(query) )
        tickers = res.json()
        krw_tickers = [x['market'] for x in tickers if 'KRW-' in x['market'] ]
        return krw_tickers

    def get_candles(self,ticker='KRW-BTC',unit='minutes',count=12,min_unit=60,to=datetime.now()):
        if unit == 'minutes':
            url = self.server_url + f"/v1/candles/minutes/{min_unit}"
        elif unit == 'days' or unit == 'weeks' or unit =='months':
            url = self.server_url +  f"/v1/candles/{unit}"
        else:
            print(f"Error : incorrect unit value : {unit}")
            return None

        query = { 'market' : ticker , 'count' : count , 'to':to.strftime('%Y-%m-%d %H:%M:%S')}

        res = requests.get(url, params=query, headers=self.get_header(query) )
        res_json = res.json()
        candle_df = pd.DataFrame(res_json)
        if(unit=='minutes'):
            candle_df['change'] = (candle_df['trade_price'] - candle_df['opening_price']) / candle_df['opening_price'] * 100
            candle_df['slope'] = (candle_df['trade_price'] - candle_df['opening_price']) / min_unit / candle_df['opening_price'] * 100
        candle_df = candle_df.sort_values('candle_date_time_kst').reset_index(drop=True)
        #candle_df.sort_values('candle_date_time_kst')
        return candle_df

    def find_change_all(self,unit='minutes', min_unit=3,to=datetime.now(),change='volume'):
        target_df = self.get_all_market();
        key =''
        if change == 'volume':
            key = 'candle_acc_trade_volume'

        for m in target_df.market:
            #print(f"market : {m}")
            
            candle_df = self.get_candles(ticker=m, unit=unit,min_unit=min_unit,count=2,to=to) 
            prev = (candle_df.loc[0,'candle_acc_trade_volume'])
            now = (candle_df.loc[1,'candle_acc_trade_volume'])
            
            if prev * 20 < now:
                print(f"{m} there is meaningful change in {key} , prev : {prev}, now {now}")
            time.sleep(0.05)
            
        

    def get_current_rsi(self,_ticker='KRW-BTC',_period=14):
        candle_df = self.get_candles(ticker=_ticker, unit='days', count=_period) 
        au= candle_df[candle_df['change_rate'] > 0]['change_rate'].mean()
        ad= candle_df[candle_df['change_rate'] < 0]['change_rate'].mean()

        rs = au/abs(ad)
        rsi = rs/(1+rs) * 100
        if rsi >= 70:
            print('selling signal on  %s rsi ' % _ticker)
        elif rsi <= 30: 
            print ('buying signal on %s rsi' % _ticker)
        return rsi

    def check_rsi(self,_ticker='KRW-BTC'):
        print("Ticker %s" % _ticker)
        rsi = self.get_current_rsi(_ticker)
        if rsi >= 70 :
            print(f"rsi indicator is high: {rsi}")
            return False
        elif rsi <= 30:
            print(f"rsi indicator is low  : {rsi}")
            return True

    def get_all_market(self,krw_only=True):
        url = self.server_url +  f"/v1/market/all"
        query = { 'isDetails' : True }
        res = requests.get(url, params=query, headers=self.get_header(query) )
        res_json = res.json()
        market_df = pd.DataFrame(res_json)
        if krw_only:
            market_df = market_df[market_df['market'].str.contains('KRW-')]
            market_df = market_df.reset_index()
        return market_df
        
    def check_falling(self,_ticker='KRW-BTC',_unit='days'):
        if _unit  == 'minutes':
            candle_df = self.get_candles(ticker=_ticker, unit=_unit, min_unit=15,count=100)
        else:
            candle_df = self.get_candles(ticker=_ticker, unit=_unit,count=100)
        current_df = candle_df.tail(10)
        min_change_idx = current_df['change'].idxmin()
        min_price_idx = current_df['low_price'].idxmin()
        avg_change = candle_df['change'].apply(abs).mean()
        last_change = current_df.iloc[9]['change']

        print(f"avg change : {avg_change}, last change : {last_change}")
        if last_change < 0 and abs(last_change) >  5 * avg_change and min_price_idx == 9:
            self.tbot.broadcast(f"{_ticker} is falling!")
            return True
        else:
            return False

    def get_stochastic(self,_ticker='KRW-BTC'):
        '''
            stochastic use 2 indicators
            1. %K(Fast-K?) = (Today's last price - min_price(5days) ) / ( max_price(5d) - min_price(5d) ) * 100
            2. %D(Slow?) = Average of %k for m days ( In stock market m is 3? )
            2~6
            1~5
            0~4
            If we want to find Rigth Crossover - After K arrives the point, D Crossover
            If k is under 20, oversold. -> buying time
            If k is over 80, overbought -> selling time.
            just kept last K and D? think this is just for day. not for realtime. 

            Case 1. Golden Cross
                Prev (k,d) ( 10, 15) -> now (k,d) (20,18)
            Case 2. Death Cross
                Prev (k,d) ( 90, 85) -> now (k,d) (80,82)
        '''
        _d=5
        _m=3
        candle_df = self.get_candles(ticker=_ticker, unit="days",count=7) 
        darr=[]
        fast_k = 0.0
        sum_d =0.0
        for i in range(0,_m):
            target_df = candle_df.iloc[i:i+_d]
            k = ( target_df['trade_price'].iloc[_d-1]-target_df['low_price'].min() ) / ( target_df['high_price'].max() - target_df['low_price'].min() ) *100
            if i == _m-1:
                fast_k = k 
            sum_d += k
        slow_d = sum_d/_m
        print(f"k: {k}, Fast K : {fast_k}, slow D : {slow_d}")
        self.k = fast_k
        self.d = slow_d
        
            
        ''' 
        print(f" in get stochastic  Expect highs : {candle_df['high_price']} ,{candle_df['high_price'].max()}" )
        print(f" in get stochastic  Expect highs : {candle_df['low_price']}, {candle_df['low_price'].min()}" )
        print(f" in get stochastic  Expect last day : {candle_df.iloc[4]}") 
        '''



