import pandas as pd
import os
from datetime import datetime 
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException


class BrokerAPI:
    def __init__(self,creds:dict,isIsolated='FALSE'):

        self.apiKey = creds['api_key']
        self.apiSecret = creds['api_secret'] 
        self.tld = creds['tld']
        self.isIsolated = isIsolated

    def connect(self):
        """
        connects to broker api\n
        """
        self.api = Client(
            api_key = self.apiKey,
            api_secret = self.apiSecret,
            tld = self.tld
        )
        status = self.api.get_system_status()
        if int(status['status']) == 0:
            print('logged in')

    def get_account_balance(self,symbol,asset='USDT'):
        """
        returns account balance\n
        """
        # res = self.api.get_account() 
        # # find asset balance in list of balances
        try:
        #     if "balances" in res:
        #         for bal in res['balances']:
        #             if bal['asset'].lower() == asset.lower():
        #                 balance = bal['free']
        #                 break 
        #         return float(balance)
        #     else:
        #         return None
            if not self.isIsolated:
                info = self.api.get_margin_account()['userAssets']
                for item in info :
                    if item['asset'] == asset :
                        balance = item['free']
                return float(balance)
            else:
                info = self.api.get_isolated_margin_account()['assets']
                for asset in info:
                    if asset['quoteAsset']['asset'] == 'USDT':
                        balance = asset['quoteAsset']['free']
                        break
                return float(balance)
        except Exception as e:
            print(e)
            return None

    def get_ticker(self,symbol):
        """
        returns current market values for symbol
        """
        try:
            res = self.api.get_ticker(symbol=symbol)
            return res
        except:
            return None

    def place_short_order(self,symbol:str,side:str,quantity:float,type:str='MARKET',timeInForce:str='GTC',price=None,sideEffectType:str='AUTO_REPAY'):
        """
        places order in broker server\n
        returns dictionary 
        """
        try:

            if type == 'MARKET':
                order = self.api.create_margin_order(
                    symbol = symbol, 
                    side = side, 
                    type = type, 
                    quantity = quantity, 
                    isIsolated = self.isIsolated,
                    sideEffectType = sideEffectType,
                    ) 
            elif type == 'LIMIT':
                order = self.api.create_margin_order(
                symbol = symbol,
                side = side,
                type = type,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                sideEffectType = sideEffectType,
                timeInForce = timeInForce
                ) 
            elif type == 'STOP_LOSS':
                order = self.api.create_margin_order(
                symbol = symbol,
                side = side,
                type = ORDER_TYPE_STOP_LOSS_LIMIT, 
                stopPrice = price,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                sideEffectType = sideEffectType,
                timeInForce = timeInForce
                ) 
            elif type == 'TAKE_PROFIT':
                order = self.api.create_margin_order( 
                symbol = symbol,
                side = side,
                type = ORDER_TYPE_TAKE_PROFIT_LIMIT,
                stopPrice = price,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                sideEffectType = sideEffectType,
                timeInForce = timeInForce
                ) 
            #print(order,'\n')
            return order 

        except BinanceOrderException as e:
            print(e)
            return None
        except BinanceAPIException as e:
            print(e)
            return None

    def place_long_order(self,symbol:str,side:str,quantity:float,type:str='MARKET',timeInForce:str='GTC',price=None):
        """
        places order in broker server\n
        returns dictionary 
        """
        try:

            if type == 'MARKET':
                order = self.api.create_margin_order(
                    symbol = symbol, 
                    side = side, 
                    type = type, 
                    quantity = quantity, 
                    isIsolated = self.isIsolated
                    ) 
            elif type == 'LIMIT':
                order = self.api.create_margin_order(
                symbol = symbol,
                side = side,
                type = type,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                timeInForce = timeInForce
                ) 
            elif type == 'STOP_LOSS':
                order = self.api.create_margin_order(
                symbol = symbol,
                side = side,
                type = ORDER_TYPE_STOP_LOSS_LIMIT, 
                stopPrice = price,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                timeInForce = timeInForce
                ) 
            elif type == 'TAKE_PROFIT':
                order = self.api.create_margin_order( 
                symbol = symbol,
                side = side,
                type = ORDER_TYPE_TAKE_PROFIT_LIMIT,
                stopPrice = price,
                price = price,
                quantity = quantity,
                isIsolated = self.isIsolated,
                timeInForce = timeInForce
                ) 
            #print(order,'\n')
            return order 

        except BinanceOrderException as e:
            print(e)
            return None
        except BinanceAPIException as e:
            print(e)
            return None

    def cancel_order(self,symbol,orderId):
        """
        Cancels the order if it not filled\n
        """
        try: 
            #o = self.api.get_open_margin_orders(symbol=symbol)
            self.api.cancel_margin_order(symbol=symbol,orderId=orderId)
        except Exception as e:
            print(e)

    def cancel_all_orders(self,symbol):
        """
        cancels all open orders
        """
        o = self.api.get_open_margin_orders(symbol=symbol)
        for order in o:
            self.api.cancel_margin_order(symbol=order['symbol'],orderId=order['orderId'])
        pass

    def query_order(self,symbol,orderId):
        """
        Get query of the order\n
        """
        o = self.api.get_margin_order(symbol=symbol,orderId=orderId)
        return o

if __name__ == '__main__':

	import json
	with open(os.path.join(os.path.dirname(__file__),'credentials.json')) as f:
		creds = json.load(f)
		f.close()

	api = BrokerAPI(creds,False)