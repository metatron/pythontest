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
    def __init__(self, coin="BTC_JPY", tokenId=5, key="", secret="", code=""):
        super().__init__(coin, key, secret)

        self._data = json.dumps({"product_code":coin}).encode("utf-8")
        self._url = "https://api.quoine.com"
        self.token_id = tokenId

        # prep headers
        auth_payload = {
            'path': self._url,
            'nonce': str(int(time.time())),
            'token_id': self.token_id
        }
        encoded_jwt = jwt.encode(auth_payload, secret, algorithm='HS256')

        request_headers = {
            'X-Quoine-API-Version': '2',
            'X-Quoine-Auth': encoded_jwt,
            'Content-Type': 'application/json'
        }

        self._code = code
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
            return

        if size == 0:
            print("************ [orderCoinRequest] size is 0!")
            return

        if side == None:
            print("************ [orderCoinRequest] side is None!")
            return

        params = {
            "product_id": self.token_id,
            "order_type": "limit",
            "side": side,
            "price": coinPrice,
            "quantity": size,
        }

        path = "/orders"
        resultJson = self._getRequestData(path, params)
        if resultJson == None:
            print("************ [orderCoinRequest] request Error!")
            return

        orderId = resultJson['id']
        if orderId == None or orderId == "":
            print("************ [orderCoinRequest] orderId Error!")
            return

        print("*** [orderCoinRequest] {} order sent. price:{}, size:{}".format(side, coinPrice, size))


if __name__ == '__main__':
    quoinex = QuoinexController()
    quoinex.getProducts()
