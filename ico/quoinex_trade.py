#!/usr/bin/env python
# coding=utf-8

import json
from datetime import datetime
import hmac
import requests
import hashlib

import time
import json
import jwt
import requests
import datetime

from ico.bitflyer_trade import BitFlyerController


TICK_POS_DATE = 0
TICK_POS_PRICE = 1
TICK_POS_VOLUME = 2

NEWEST_TICK_POS = -1

# メモリー制限の為保持できるtickのサイズを決める
MAX_TICKLIST_SIZE = 20000

CANDLE_POS_OPEN = 0
CANDLE_POS_HIGH = 1
CANDLE_POS_LOW = 2
CANDLE_POS_CLOSE = 3
CANDLE_POS_VOLUME = 4


class QuoinexController(BitFlyerController):
    """
    :param key
    :param secret
    :param code 2段階認証
    """
    def __init__(self, coin="BTC_JPY", key="", secret="", code=""):
        super().__init__(coin, key, secret)

        self._url = "https://api.quoine.com"
        self.token_id = key

        self._initParams()

        crntDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        self._tickFilePath = "./csv/tick_quoinex_" + str(crntDateTime) + "_" + self._coin + ".csv"




    """
        トレードの種類取得。
        (BTCJPYはID 5)
        ask: 売り
        bid: 買い
    """
    def getProducts(self):
        path = "/products"
        resultJson = self._getRequestData(path)
        print(json.dumps(resultJson))


    def getTickData(self):
        path = "/products/5"
        resultJson = self._getRequestData(path)
        self._addToTickList(resultJson["market_bid"], resultJson['volume_24h'])
        self._convertTickDataToCandle(self._tickList)


    def getBalance(self):
        path = "/accounts/balance"
        resultJson = self._getRequestData(path)
        print(json.dumps(resultJson))


    def checkOrder(self, orderId):
        path = "/orders/{}".format(orderId)
        resultJson = self._getRequestData(path)
        status = resultJson['status']

        print(json.dumps(resultJson))

        return status


    def cancelOrder(self, orderId):
        path = "/orders/{}/cancel".format(orderId)
        resultJson = self._getRequestData(path)
        print(json.dumps(resultJson))


    """
        売買注文を出す。

        :param side "BUY", "SELL"
        :param coinPrice 値段
        :param size 個数
        :param expireMin (Quoinexでは未使用）
    """
    def orderCoinRequest(self, side, coinPrice, size, expireMin=180):
        if coinPrice == 0:
            print("************ [orderCoinRequest] coinPrice is 0!")
            return 0

        if size == 0:
            print("************ [orderCoinRequest] size is 0!")
            return 0

        if side == None:
            print("************ [orderCoinRequest] side is None!")
            return 0

        params = {
            "order": {
                "product_id": 5,
                "order_type": "limit",
                "side": side,
                "price": coinPrice,
                "quantity": size,
            }
        }

        params = json.dumps(params)

        path = "/orders/"
        resultJson = self._getRequestData(path, params=params, getOrPost='post')

        if resultJson == None:
            print("************ [orderCoinRequest] request Error!")
            return

        orderId = resultJson['id']
        if orderId == None or orderId == "":
            print("************ [orderCoinRequest] orderId Error!")
            return

        print("*** [orderCoinRequest] {} order sent. orderId:{}, price:{}, size:{}".format(side, orderId, coinPrice, size))

        return orderId


    def autoBuy(self):
        self.getTickData()
        crntPrice = self._tickList[NEWEST_TICK_POS][TICK_POS_PRICE]
        self.orderCoinRequest("buy", crntPrice, 0.001)


    def autoSell(self):
        self.getTickData()
        crntPrice = self._tickList[NEWEST_TICK_POS][TICK_POS_PRICE]
        self.orderCoinRequest("sell", crntPrice, 0.001)


    def _getRequestData(self, path, params=None, getOrPost='get'):
        # prep headers
        auth_payload = {
            'path': path,
            'nonce': str(int(time.time()*1000)),
            'token_id': self.token_id
        }
        encoded_jwt = jwt.encode(auth_payload, self._secret, algorithm='HS256')

        self._headers = {
            'X-Quoine-API-Version': '2',
            'X-Quoine-Auth': encoded_jwt,
            'Content-Type': 'application/json'
        }

        if(getOrPost == 'get'):
            res = requests.get(self._url+path, headers=self._headers, params=params)
        else:
            res = requests.post(self._url+path, data=params, headers=self._headers)

        if res.status_code == 200:
            resultJson = json.loads(res.text)
            return resultJson
        else:
            print("Error Code:{}, Msg:{}".format(res.status_code, res.content))
        return None






if __name__ == '__main__':
    quoinex = QuoinexController(key="", secret="")
    # quoinex.getBalance()
    # orderId = quoinex.orderCoinRequest("buy", 872052.0, 0.001)
    # quoinex.checkOrder(orderId)
    # quoinex.orderCoinRequest("sell", 862223, 0.001)
    # orderId = quoinex.orderCoinRequest("sell", 873052.0, 0.001)
    # quoinex.checkOrder(232363447)

    # quoinex.autoBuy()
    # quoinex.autoSell()
    # quoinex.cancelOrder();


