import json, time, os
from threading import Thread
from bin.api_caller import BrokerAPI

class Bot(Thread) :

    def __init__(self,creds, settings):
        Thread.__init__(self)

        self.marginType = settings['margin_type']

        self.api = BrokerAPI(creds,settings['margin_type'])
        self.api.connect()

        #settings 
        self.orderType = settings['type']
        #self.takeProfitLevels = settings['take_profit_levels']
        self.lastTakeProfit = settings['enable_take_profits_upto']
        self.quantity = settings['quantity']
        self.timeInForce = settings['time_in_force']
        self.takeProfitQuantity = settings['quantity_per_take_profit']
        self.takeProfitPrices = settings['take_profits']
        self.stopLossEnabler = bool(settings['stop_loss_switch'])
        self.stopLossType = settings['stoploss_type']
        #self.stopPercent = settings['stop_loss_percent']/100
        self.stoploss = settings['stop_loss']

        self._positions = dict()#dictionary to save all orders placed by BOT

    def update_attributes(self,settings):
        """
        updates class attributes on runtime
        """
        print('\nupdating attributes\n')
        self.marginType = settings['margin_type'] 
        self.orderType = settings['type']
        self.quantity = settings['quantity'] 
        self.timeInForce = settings['time_in_force']
        #self.takeProfitLevels = settings['take_profit_levels']
        self.lastTakeProfit = settings['enable_take_profits_upto']
        self.takeProfitQuantity = settings['quantity_per_take_profit']
        self.takeProfitPrices = settings['take_profits']
        self.stopLossEnabler = bool(settings['stop_loss_switch'])
        self.stopLossType = settings['stoploss_type']
        self.stoploss = settings['stop_loss']
        time.sleep(1)
        print('\nattributes updated')

    def read_alert(self,alert):
        """
        Read the alert received from webhook and filter\n
        """
        symbol = alert['ticker']
        side = alert['side']
        price = alert['close']
        quantity = self.quantity
        type=self.orderType
        timeInForce=self.timeInForce

        if side in ['buy','BUY','long','LONG']:
            side = 'BUY'
        elif side in ['sell','SELL','short','SHORT']:
            side = 'SELL'
        else:
            pass

        print(f'alert recieved for {symbol} in bot and now filtering for placing order')
        
        if symbol not in self._positions.copy():

            if side == 'BUY':
            
                order = self.api.place_long_order(
                                    symbol=symbol, 
                                    side=side,
                                    quantity=self.quantity,
                                    type=type, 
                                    timeInForce=timeInForce,
                                    price=price)
            else:
                order = self.api.place_short_order(
                                    symbol=symbol, 
                                    side=side,
                                    quantity=self.quantity,
                                    type=type, 
                                    timeInForce=timeInForce,
                                    sideEffectType='MARGIN_BUY',
                                    price=price)

            if order:
                self._positions.update({
                    symbol : { 
                        'entryOrder' : order,
                        'entryPrice' : price,
                        'profitBookedFor' : 0,
                        'entryFilled' : False,
                        'takeProfitPrices' : self.takeProfitPrices,
                        'takeProfitQuantity' : self.takeProfitQuantity,
                        'lastTakeProfit' : self.lastTakeProfit
                    }
                })
                print('entry order placed')
                if self.stopLossEnabler: 
                    self._positions[symbol].update({
                        'stopLossType' : self.stopLossType,
                        'stoploss' : self.stoploss
                    })
                    
        else:
            # self.check_exits(symbol)
            # if symbol in self._positions.copy(): 
            entryQty = float(self._positions[symbol]['entryOrder']['origQty'])
            executedQty = self._positions[symbol]['profitBookedFor'] 

            quantity = entryQty - executedQty 

            if side == 'BUY':
                order = self.api.place_short_order(symbol,side,quantity,timeInForce=self.timeInForce)
                print('position closed')
            else:
                order = self.api.place_long_order(symbol,side,quantity,timeInForce=self.timeInForce)
                print('position closed') 

            takeProfitOrders = self._positions[symbol]['takeProfitOrders'] 
            
            for order in takeProfitOrders:
                o = self.api.query_order(symbol,order['orderId'])
                if o['status'] == 'NEW':
                    self.api.cancel_order(symbol,order['orderId'])

            if 'stoplossOrder' in self._positions[symbol]:
                order = self._positions[symbol]['stoplossOrder'] 
                o = self.api.query_order(symbol,order['orderId'])
                if o['status'] =='NEW':
                    self.api.cancel_order(symbol,order['orderId'])

            del self._positions[symbol]

    def trail_stoploss(self,symbol):
        """
        trails stoploss on the stoploss price given
        """
        takeProfitOrders = self._positions[symbol]['takeProfitOrders'] 
        symbolInfo = self.api.get_ticker(symbol)
        lastPrice = float(symbolInfo['lastPrice'])
        currentStop = self._positions[symbol]['currentStop'] 
        side = self._positions[symbol]['entryOrder']['side'] 
        if side == 'BUY':
            if lastPrice <= currentStop:
                quantity = float(self._positions[symbol]['stoplossOrder']['origQty'])
                self.api.place_long_order(symbol,'SELL',quantity)
                for order in takeProfitOrders:
                    self.api.cancel_order(symbol,order['orderId'])
                del self._positions[symbol]
            elif abs(currentStop-lastPrice) > self._positions[symbol]['stoploss']:
                self._positions[symbol]['currentStop'] = currentStop + (abs(currentStop-lastPrice)-self._positions[symbol]['stoploss'])       
        
        else:
            if lastPrice >= currentStop:
                quantity = float(self._positions[symbol]['stoplossOrder']['origQty'])
                self.api.place_short_order(symbol,'BUY',quantity)
                for order in takeProfitOrders:
                    self.api.cancel_order(symbol,order['orderId']) 
                del self._positions[symbol]
            elif abs(currentStop-lastPrice) > self._positions[symbol]['stoploss']:
                self._positions[symbol]['currentStop'] = currentStop - (abs(currentStop-lastPrice)-self._positions[symbol]['stoploss'])

    def check_exits(self,symbol):
        """
        checks if any take profit or stoploss is executed\n
        updates positions if it is so\n
        """
        try:
            takeProfitOrders = self._positions[symbol]['takeProfitOrders'] 
            for order in takeProfitOrders:
                o = self.api.query_order(symbol,order['orderId'])
                if o['status'] not in ['NEW']:
                    self._positions[symbol]['takeProfitOrders'].remove(o)
                    self._positions[symbol]['profitBookedFor'] += float(o['origQty'])

                    if len(self._positions[symbol]['takeProfitOrders']) == 0:
                        if 'stoplossOrder' in self._positions[symbol]:
                            order = self._positions[symbol]['stoplossOrder'] 
                            self.api.cancel_order(symbol,order['orderId']) 
                        del self._positions[symbol]

                elif o['status'] in ['NEW']:
                    break

            if 'stoplossOrder' in self._positions[symbol] and symbol in self._positions:
                order = self._positions[symbol]['stoplossOrder'] 
                o = self.api.query_order(symbol,order['orderId']) 
                if o['status'] not in ['NEW']:
                    for order in takeProfitOrders:
                        self.api.cancel_order(symbol,order['orderId'])
                    del self._positions[symbol]

        except Exception as e:
            print(e)

    def run(self):

        print('Bot started...')

        while True:
            try:
                for symbol in self._positions.copy():
                    if not self._positions[symbol]['entryFilled']:
                        orderId = self._positions[symbol]['entryOrder']['orderId']
                        order = self.api.query_order(symbol,orderId)
                        if order['status'] in ['FILLED', 'PARTIALLY_FILLED']:
                            self._positions[symbol]['entryFilled'] = True
                            entryPrice = self._positions[symbol]['entryPrice']
                            totalQty = float(self._positions[symbol]['entryOrder']['origQty'])
                            side = self._positions[symbol]['entryOrder']['side'] 

                            if 'stopLossType' in self._positions[symbol]:
                                if side == 'BUY':
                                    stopSide = 'SELL' 
                                    stopPrice = entryPrice - self._positions[symbol]['stoploss']
                                    stoplossOrder = self.api.place_long_order(symbol,stopSide,totalQty,'STOP_LOSS',price=stopPrice)
                                else:
                                    stopSide = 'BUY'
                                    stopPrice = entryPrice + self._positions[symbol]['stoploss']
                                    stoplossOrder = self.api.place_short_order(symbol,stopSide,totalQty,'STOP_LOSS',price=stopPrice)

                                if stoplossOrder:
                                    self._positions[symbol].update({
                                        'stoplossOrder' : stoplossOrder,
                                        'currentStop' : stopPrice
                                    })
                                    print('stoploss order placed') 

                            takeProfitPrices = self._positions[symbol]['takeProfitPrices']
                            takeProfitQty = float(self._positions[symbol]['takeProfitQuantity'])
                            for p in takeProfitPrices:
                                if totalQty != 0 and (takeProfitPrices.index(p)+1) <= self.lastTakeProfit:
                                    if side == 'BUY':
                                        stopSide = 'SELL' 
                                    else:
                                        stopSide = 'BUY' 

                                    if stopSide == 'BUY':
                                        price  = entryPrice - float(p)
                                        order = self.api.place_short_order(symbol,stopSide,takeProfitQty,'TAKE_PROFIT',price=price)
                                    else:
                                        price  = entryPrice + float(p)
                                        order = self.api.place_long_order(symbol,stopSide,takeProfitQty,'TAKE_PROFIT',price=price) 

                                    totalQty -= takeProfitQty 

                                    if order:
                                        if 'takeProfitOrders' not in self._positions[symbol]:
                                            self._positions[symbol].update({
                                                'takeProfitOrders' : [order]
                                            })
                                            print(f'take profit {(takeProfitPrices.index(p)+1)} placed')
                                        else:
                                            self._positions[symbol]['takeProfitOrders'].append(order)
                                            print(f'take profit {(takeProfitPrices.index(p)+1)} placed')

                        elif order['status'] in ['CANCELED','PENDING_CANCEL','REJECTED','EXPIRED']:
                            del self._positions[symbol]
                    else:
                        self.check_exits(symbol)
                        if 'stopLossType' in self._positions[symbol]:
                            if self._positions[symbol]['stopLossType'] == 'TRAILING_STOPLOSS':
                                self.trail_stoploss(symbol)

            except Exception as e:
                print(e)
                continue

if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__),'credentials.json')) as f:
        creds = json.load(f)
        f.close()

    with open(os.path.join(os.path.dirname(__file__),'settings.json')) as f:
        settings = json.load(f)
        f.close()

    # Creating bot instance
    Bot1 = Bot(creds=creds, settings=settings)
    #Bot started in thread 
    #Bot1.start()

