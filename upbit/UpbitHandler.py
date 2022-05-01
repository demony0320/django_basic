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
import traceback

class UpbitHandler:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):         
            cls._instance = super().__new__(cls)  
        return cls._instance                      

    def __init__(self):
        cls = type(self)
        if not hasattr(cls, "_init"):             
            #self.data = data
            cls._init = True
            self.load_config()
            self.tbot = Tbot(self.telegram_token ,self.telegram_target)
            self.markets = self.get_all_market()
            self.monitor_list= []
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
    '''
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
        '''

    def get_candles(self,ticker='KRW-BTC',unit='minutes',count=12,min_unit=60,to=datetime.now()):
        try:
            if unit == 'minutes':
                url = self.server_url + f"/v1/candles/minutes/{min_unit}"
            elif unit == 'days' or unit == 'weeks' or unit =='months':
                url = self.server_url +  f"/v1/candles/{unit}"
            else:
                    
                print(f"Error : incorrect unit value : {unit}")
                raise Exception(f"incorrect unit : {unit}")
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
        except Exception as e :
            print ("get_candles Exception occurs : ", e, traceback.format_exc())
            raise e
            

    def get_volume_change(self,unit='minutes', min_unit=5,to=datetime.now(),change='volume'):
        target_df = self.markets
        results = []
        key =''
        if change == 'volume':
            key = 'candle_acc_trade_volume'
        for m in target_df.market:
            #print(f"market : {m}")
            
            candle_df = self.get_candles(ticker=m, unit=unit,min_unit=min_unit,count=2,to=to) 
            prev_vol = (candle_df.loc[0,'candle_acc_trade_volume'])
            now_vol = (candle_df.loc[1,'candle_acc_trade_volume'])
            prev_high_price = (candle_df.loc[0,'high_price'])
            now_price = (candle_df.loc[1,'trade_price'])
            acc_price =  (candle_df.loc[1,'candle_acc_trade_price'] )
            if prev_vol * 55 <=  now_vol and acc_price >= 100000000 and prev_high_price < now_price:
                print(f"{m} there is meaningful change in {key} , vol change : {prev_vol}->{now_vol} Acc_price : {acc_price}")
                print(f" prev high price : {prev_high_price}, now_price : {now_price}")
                result = { "ticker" : m , "msg" :  f"there is meaningful change in {key} : {prev_vol}->{now_vol}, price : {prev_high_price}->{now_price}"}
                results.append(result)
            time.sleep(0.05)
        return results
            
    def get_momentum(self, _ticker='KRW-BTC', m_df=None):
        if m_df is None:
            m_df = self.get_candles(ticker=_ticker, unit='months',count=7) 
        if len(m_df) != 7:
            raise Exception("momentum candles length should be 7")
        c_price = m_df.iloc[6]['trade_price']
        returns =[]
        for i in [0,3,5]:
            start_price =  m_df.iloc[i]['trade_price']
            returns.append( (c_price - start_price)/start_price )
        m = (sum(returns) / 3 )* 100
        print(f"in the get momentum : {m}")
        return m , m > 0 

    def get_rsi(self,_ticker='KRW-BTC',_period=14,_action='BUY',candle_df=None):
        '''
            need to enhance based on hashnet wiki
            real buying signal would like, 20-> 25->30 ( need to check change!)
        '''
        if candle_df is None:
            candle_df = self.get_candles(ticker=_ticker, unit='days', count=_period) 
        if len(candle_df) !=14:
            raise Exception("rsi need 14 length dataframe!")
        au= candle_df[candle_df['change_rate'] > 0]['change_rate'].mean()
        ad= candle_df[candle_df['change_rate'] < 0]['change_rate'].mean()

        rs = au/abs(ad)
        rsi = rs/(1+rs) * 100
        if rsi >= 70 and _action == 'SELL':
            print('selling signal on  %s rsi ' % _ticker)
            return rsi, True
        elif rsi <= 30 and _action == 'BUY': 
            print ('buying signal on %s rsi' % _ticker)
            return rsi, True
        return rsi, False

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

    def get_stochastic(self,_ticker='KRW-BTC',_action = 'BUY',candle_df=None):
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
        if candle_df is None:
            candle_df = self.get_candles(ticker=_ticker, unit="days",count=7) 
        if len(candle_df) != 7:
            raise Exception("stochastic candles length should be 7")
        karr=[]
        last_k = 0.0
        sum_d =0.0
        for i in range(0,_m):
            target_df = candle_df.iloc[i:i+_d]
            k = ( target_df['trade_price'].iloc[_d-1]-target_df['low_price'].min() ) / ( target_df['high_price'].max() - target_df['low_price'].min() ) *100
            if i == _m-1:
                last_k = k 
            sum_d += k
            karr.append(k)
        slow_d = sum_d/_m
        print(f"ticker : {_ticker}, karr : {karr} , Fast K : {last_k}, slow D : {slow_d}")
        # if ith item of karr is smaller than 20, slow_d, check items that has bigger indexs whether bigger than slow_d
        if _action == 'BUY':
            low_idx = -1 
            for i,val in enumerate(karr):
                if val <= 20  and val <= slow_d:
                    low_idx = i
            if low_idx != -1:
                eval_k = karr[len(karr)-1] 
                if eval_k > slow_d:
                    return last_k, slow_d, True
            return last_k, slow_d, False
        elif _action == 'SELL':
            high_idx = -1
            for i, val in  enumerate(karr):
                if val >= 20 and val >= slow_d:
                    high_idx = i
            if high_idx != -1:
                eval_k = karr[len(karr)-1]
                if eval_k < slow_d:
                    return last_k, slow_d, True

        return last_k,slow_d, False

    def get_adi(self,ticker='KRW-BTC',day=10,df=None):
        '''
            sum of (  (( close - low) - ( high - low ) ) /(high-low) * volume )
            need detailed information..
            need analysis (value of sudden raise tickers)
        '''
        if df is None or len(df) != day * 4:
            df = self.get_candles(ticker=ticker, unit='minutes', min_unit=240, count= day * 4)
        adi_arr = []
        day_sum =0 
        _signal = False
        for i,row in df.iterrows():
            #print (i,row)
            day_sum +=((( row['trade_price'] - row['low_price'] ) - ( row['high_price'] - row['low_price'] ) ) / ( row['high_price'] - row['low_price'] )) * row['candle_acc_trade_volume'] 
            if ( i+1 ) % 4 == 0:
                adi_arr.append(day_sum)
                day_sum =0
        abs_mean = sum(list(map(abs, adi_arr[:-1])))/len(adi_arr[:-1])
        if adi_arr[-1] > abs_mean*2:
            _signal = True    
        return adi_arr, _signal

    def get_chaikin (self,_ticker='KRW-BTC',df=None):
        '''
        Oscillator 
        avg( 3days EMA(adi)) - avg( 10 days of EMA(adi))
        3 and 10 can be adjusted. cause crypto currency moves faster than general stock
        '''
        long_period= 10
        short_period= 3
        if df is None or len(df) != day * 4:
            df = self.get_candles(ticker=_ticker, unit='minutes', min_unit=240, count= long_period * 4)


        #Let's get Divergence between chaikin and price change ( last day)  

        long_adi_arr , adi_flag = self.get_adi(ticker=_ticker,df=df)
        short_adi_arr = long_adi_arr[:3]
        long_exp = 2/(1+long_period)
        short_exp = 2/(1+short_period)
        long_ema_avg = long_exp * long_adi_arr[-1] + (1-long_exp) *  ( sum(long_adi_arr[:-1])/len(long_adi_arr[:-1]) )
        short_ema_avg = short_exp * short_adi_arr[-1] + (1-short_exp) *  ( sum(short_adi_arr[:-1])/len(short_adi_arr[:-1]) )
        chaikin = ( short_ema_avg - long_ema_avg) / long_ema_avg 
        chaikin_flag = False
        if ( df.iloc[-1]['trade_price'] - df.iloc[-4]['opening_price'] ) < 0 and chaikin > 0:
            chaikin_flag=True

        return chaikin, chaikin_flag

    def runner_long( self, momentum_flag=True, stochastic_flag=True, rsi_flag=True):
        '''
            month candles = momentum
            day candle = rsi, stochastic
            
            maybe need child process to run this function.
        '''
        d_period = 7
        m_period = 7 
        # get candles 

        for m in self.markets :
            #m_dict= {}
            m_dict['name']=m
            if momentum_flag:
                m_df = self.get_candles(ticker=m, unit='months',count=m_period)                
            if rsi_flag or stochastic_flag:
                if rsi_flag:
                    d_period = 14
                d_df = self.get_candles(ticker=m, unit='days', count=d_period) 

            if momentum_flag:
                m_val, m_bool = get_momentum(m,m_df)
                if m_bool:
                    m_dict['momentum'] = m_val
            if stochastic_flag:
                s_k,s_d,s_bool = get_stochastic(_ticker=m,_df=d_df[7:])
                if s_bool:
                    m_dict['stochastic'] = { "K" : s_k , "D" : s_d }
            if rsi_flag:
                r, r_bool = get_rsi(_ticker=m, _df=d_df)
                if r_bool:
                    m_dict['rsi'] = r
            if (momentum_flag and 'momentum' in m) or ( not momentum_flag ) and (stochastic_flag and 'stochastic' in m) or (not stochastic_flag) and (rsi_flag and 'rsi' in m) or (not rsi_flag):
                m_dict['dt']=datetime.now()
                print(m_dict)
                self.monitor_list.append(m_dict)

            time.sleep(0.05)




            
        
            
        ''' 
        print(f" in get stochastic  Expect highs : {candle_df['high_price']} ,{candle_df['high_price'].max()}" )
        print(f" in get stochastic  Expect highs : {candle_df['low_price']}, {candle_df['low_price'].min()}" )
        print(f" in get stochastic  Expect last day : {candle_df.iloc[4]}") 
        '''



