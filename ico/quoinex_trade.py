import json
from datetime import datetime
import hmac
import requests
import hashlib

import time
import json
import jwt
import requests

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
        super().__init__(self, coin, key, secret)

        self._data = json.dumps({"product_code":coin}).encode("utf-8")
        self._url = "https://api.quoine.com"

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




