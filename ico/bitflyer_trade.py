import json
from datetime import datetime
import hmac
import requests
import hashlib
import time

key = ""
secret = ""

class BitFlyerController():
    def __init__(self):
        self._data = json.dumps({"product_code":"BTC_JPY"}).encode("utf-8")
        self._url = "https://api.bitflyer.jp"

        sign = hmac.new(b'key', secret.encode('utf-8'), hashlib.sha256).hexdigest()

        self._headers = {
            'ACCESS-KEY': key,
            # 'ACCESS_TIMESTAMP' : timestamp,
            'ACCESEE-SIGN' : sign,
            'Content-Type' : 'application/json'
        }



    def getTickData(self):
        path = "/v1/ticker"
        self._headers['ACCESS_TIMESTAMP'] = str(datetime.timestamp(datetime.now()))
        res = requests.get(self._url+path, data=self._data, headers=self._headers)

        if res.status_code == 200:
            resultJson = json.loads(res.text)
            print(resultJson)



if __name__ == '__main__':
    bitflyer = BitFlyerController()

    index = 0
    isValidTime = True
    while (isValidTime):
        bitflyer.getTickData()

        time.sleep(1)

        index += 1
        if(index > 10):
            isValidTime = False
