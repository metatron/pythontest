import json
from datetime import datetime
import hmac
import requests
import hashlib
import time
import numpy as np
import math
import pandas as pd
import csv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.finance import candlestick2_ohlc
import stockstats as stss
import os
import datetime
import copy

from utils.stop_watch import stop_watch

from ico.bit_buysell_logic import BitSignalFinder

TICK_POS_DATE = 0
TICK_POS_PRICE = 1
TICK_POS_VOLUME = 2

NEWEST_TICK_POS = -1

# メモリー制限の為保持できるtickのサイズを決める
MAX_TICKLIST_SIZE = 10000

CANDLE_POS_OPEN = 0
CANDLE_POS_HIGH = 1
CANDLE_POS_LOW = 2
CANDLE_POS_CLOSE = 3
CANDLE_POS_VOLUME = 4

# これ以上の行をセーブしようとすると別ファイルになる
TICKDATA_FILE_MAXLINESIZE = 2500


class BitFlyerController():
    """
    :param key
    :param secret
    :param code 2段階認証
    """
    def __init__(self, coin="BTC_JPY", key="", secret="", code=""):
        self._coin = coin
        self._data = json.dumps({"product_code":coin}).encode("utf-8")
        self._url = "https://api.bitflyer.jp"

        sign = hmac.new(b'key', secret.encode('utf-8'), hashlib.sha256).hexdigest()

        self._headers = {
            'ACCESS-KEY': key,
            # 'ACCESS_TIMESTAMP' : timestamp,
            'ACCESEE-SIGN' : sign,
            'Content-Type' : 'application/json'
        }

        self._code = code
        self._secret = secret

        #tickデータの保存名
        self._tickFileName = "tick_bitflyer"

        self._initParams()


    def _initParams(self):
        crntDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        self._tickFilePath = "./csv/" + self._tickFileName + "_" + str(crntDateTime) + "_" + self._coin + ".csv"

        # ティックリスト
        # [時分秒,値段],...
        self._tickList = []

        # tickデータ。セーブ用に2500行しか持たない。
        # 実際の取引のは使わず、2500行に達したら別ファイルで保存を開始する。
        self._tickListForSave = []

        # ロウソク
        # [時分][open, high, low, close],...
        self._candleStats = {}
        # 前回のtickデータ。close時に使用
        self._prevTick = []

        #グラフ用
        self._fig = None
        self._ax1 = None
        self._ax2 = None

        #注文番号リスト
        self._buyIdList = []
        self._sellIdList = []



    """
        瞬間？の取引情報を取得
    """
    def getTickData(self):
        path = "/v1/ticker"
        resultJson = self._getRequestData(path)
        self._addToTickList(resultJson['ltp'], resultJson['volume_by_product'])
        self._convertTickDataToCandle(self._tickList)


    """
        板のmidpriceを取得（Tickerよりは値動きは安定）
    """
    def getBoardData(self):
        path = "/v1/board"
        resultJson = self._getRequestData(path)
        self._addToTickList(resultJson['mid_price'])
        self._convertTickDataToCandle(self._tickList)

    """
        残高情報取得
    """
    def getBalance(self):
        pass


    def checkOrder(self, orderId):
        pass


    def cancelOrder(self, orderId):
        pass


    """
        売買注文を出す。
        
        :param side "BUY", "SELL"
        :param coinPrice 値段
        :param size 個数
        :param expireMin 
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
            "product_code": self._coin,
            "child_order_type": "LIMIT",
            "side": side,
            "price": coinPrice,
            "size": size,
            "minute_to_expire": expireMin,
            "time_in_force": "GTC"
        }

        path = "/v1/me/sendchildorder"
        resultJson = self._getRequestData(path, params)
        if resultJson == None:
            print("************ [orderCoinRequest] request Error!")
            return

        orderId = resultJson['child_order_acceptance_id']
        if orderId == None or orderId == "":
            print("************ [orderCoinRequest] orderId Error!")
            return

        print("*** [orderCoinRequest] {} order sent. price:{}, size:{}".format(side, coinPrice, size))



    def lossCut(self, price):
        if(price <= 0):
            return

        #TODO 売り注文キャンセル



    """
        最大 MAX_TICKLIST_SIZE件のtickデータを保持する。
        オーバーした場合は切り捨て
    """
    def _addToTickList(self, price, volume=0):
        # tickリストに追加
        nowDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self._tickList.append([str(nowDateTime), price, volume])
        #セーブ用の配列にコピー
        self._tickListForSave.append([str(nowDateTime), price, volume])

        # メモリに乗り切らない可能性があるのでリサイズ
        startPos = max(0, len(self._tickList)-MAX_TICKLIST_SIZE)
        endPos = len(self._tickList)
        # print(startPos, endPos)
        self._tickList = self._tickList[startPos:endPos]
        # print(self._tickList)


    def _getRequestData(self, path, params=None):
        self._headers['ACCESS_TIMESTAMP'] = str(datetime.datetime.timestamp(datetime.datetime.now()))
        res = requests.get(self._url+path, data=self._data, headers=self._headers, params=params)

        if res.status_code == 200:
            resultJson = json.loads(res.text)
            return resultJson

        return None


    """"
        1分足用ArrayにTick情報を修正
    """
    def _convertTickDataToCandle(self, ticklist):
        # まだ1つしかレコードがない場合は全部現在の値段
        if len(ticklist) == 1:
            crntPrice = ticklist[0][TICK_POS_PRICE]
            crntDateTimeStr = str(ticklist[0][TICK_POS_DATE])[0:12]
            self._candleStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, 0]

            # close額設定の為保存しておく。件数制限してるため消されるかもなのでclone
            self._prevTick = ticklist[0]
            return

        # 一番最後の株価を取得
        tick = self._tickList[NEWEST_TICK_POS]
        # 分までを取得
        crntDateTimeStr = str(tick[TICK_POS_DATE])[0:12]
        crntPrice = tick[TICK_POS_PRICE]

        # 現在の時分キーが設定されてある場合、現在の株価と比較
        if crntDateTimeStr in self._candleStats:
            crntHigh = self._candleStats[crntDateTimeStr][CANDLE_POS_HIGH]
            crntLow = self._candleStats[crntDateTimeStr][CANDLE_POS_LOW]
            if crntPrice > crntHigh:
                self._candleStats[crntDateTimeStr][CANDLE_POS_HIGH] = crntPrice

            if crntPrice < crntLow:
                self._candleStats[crntDateTimeStr][CANDLE_POS_LOW] = crntPrice

            # うまくmacdなどのデータが取れないのでテスト的にここに置く。
            self._candleStats[crntDateTimeStr][CANDLE_POS_CLOSE] = crntPrice


        # 現在時分のキーが設定されてない場合は新しい時分
        else:
            # 初めて追加
            self._candleStats[crntDateTimeStr] = [crntPrice, crntPrice, crntPrice, crntPrice, 0]

            # 前時分キーのclose値をアプデ
            if self._prevTick:
                prevDateTimeStr = str(self._prevTick[TICK_POS_DATE])[0:12]
                prevClosePrice = self._prevTick[TICK_POS_PRICE]
                self._candleStats[prevDateTimeStr][CANDLE_POS_CLOSE] = prevClosePrice

        # 出来高取得（API叩く？）
        if len(tick) > 2:
            self._candleStats[crntDateTimeStr][CANDLE_POS_VOLUME] = tick[TICK_POS_VOLUME]

        # close額設定の為保存しておく
        self._prevTick = tick


    """
        self._candleStatsからstockstatsフォーマットのデータにConvertする。
    """
    def convertToStockStats(self):
        statusListGraph = []
        statDateTimeList = sorted(self._candleStats.keys())
        for statDateTime in statDateTimeList:
            status = self._candleStats[statDateTime]
            statusListGraph.append([
                statDateTime,
                float(status[CANDLE_POS_OPEN]),
                float(status[CANDLE_POS_HIGH]),
                float(status[CANDLE_POS_LOW]),
                float(status[CANDLE_POS_CLOSE]),
                float(status[CANDLE_POS_VOLUME])
            ])

        #stockstatsフォーマットにする
        pandaDataFrame = pd.DataFrame(statusListGraph, columns=['date','open','high','low','close','volume'])
        stock = stss.StockDataFrame().retype(pandaDataFrame)

        return stock


    def initGraph(self):
        # plot graph
        self._fig = plt.figure(figsize=(10, 5))
        plt.title('Stock Graph', fontsize=8)

        #一つ目
        self._ax1 = self._fig.add_subplot(1,1,1)

        # 2つ目
        self._ax2 = self._ax1.twinx()


    """
        stockstatsフォーマットのデータを受け取ってグラフを描画する。
    """
    def makeGraph(self, stockstatsClass, display=True, params=[]):
        if len(self._candleStats) <= 0:
            return

        # グラフ用
        if len(params) == 0:
            params = ['open', 'high', 'low', 'close', 'macd', 'macds', 'macdh', 'boll', 'boll_ub', 'boll_lb', 'volume']
            stockstatsClass.get("macd")
            stockstatsClass.get("macds")
            stockstatsClass.get("macdh")
            stockstatsClass.get("boll")
            stockstatsClass.get("boll_ub")
            stockstatsClass.get("boll_lb")
            stockstatsClass.get("volume")
        graphData = np.array(stockstatsClass.as_matrix(columns=params), dtype='float')

        # plt.clf()

        timetickList = []
        #x軸プロット(時間のみ[8:12]）
        timelist = sorted(self._candleStats.keys())
        for timetick in timelist:
            timetickList.append(int(timetick[8:12]))


        #x軸のラベル
        step=10
        plt.xticks([i for i in range(0, len(timetickList), step)], timetickList[::step])
        plt.xticks(rotation=25)

        open_ = graphData[:, 0]
        high_ = graphData[:, 1]
        low_ = graphData[:, 2]
        close_ = graphData[:, 3]
        candlestick2_ohlc(self._ax1, open_, high_, low_, close_, colorup="b", width=0.5, colordown="r")

        if 'boll' in params:
            ind = params.index('boll')
            boll_ = graphData[:, ind]
            self._ax1.plot(boll_, color='gray', linestyle='dashed')

        if 'boll_ub' in params:
            ind = params.index('boll_ub')
            boll_ub_ = graphData[:, ind]
            self._ax1.plot(boll_ub_, color='red', linestyle='dashed')

        if 'boll_lb' in params:
            ind = params.index('boll_lb')
            boll_lb_ = graphData[:, ind]
            self._ax1.plot(boll_lb_, color='blue', linestyle='dashed')



        self._ax2.set_ylabel('macd')

        if 'macd' in params:
            ind = params.index('macd')
            macd_ = graphData[:, ind]
            p3, = self._ax2.plot(macd_, label=r'macd', color='orange')

        if 'macds' in params:
            ind = params.index('macds')
            macds_ = graphData[:, ind]
            p3, = self._ax2.plot(macds_, label=r'macd', color='yellow')

        if 'macdh' in params:
            ind = params.index('macdh')
            macdh_ = graphData[:, ind]
            p3, = self._ax2.plot(macdh_, label=r'macd', color='grey')

        # if'volume' in params:
        #     self._ax3 = self._fig.add_subplot(2, 1, 2)
        #     ind = params.index('volume')
        #     volume_ = graphData[:, ind]
        #     p3, = self._ax3.plot(volume_, label=r'volume', color='blue')

        if display == False:
            if (os.path.exists("../figures") != True):
                os.mkdir("../figures")

            plt.savefig("../figures/candle.jpg", format="jpg", dpi=120)
        else:
            plt.pause(0.05)



    """
        ティックデータの保存
    """
    def writeTickList(self):
        # df = pd.DataFrame(self._tickList)
        df = pd.DataFrame(self._tickListForSave)
        df.to_csv(self._tickFilePath)

        # セーブファイル更新
        self.saveToNewFile()


    def saveToNewFile(self):
        if (len(self._tickListForSave) > TICKDATA_FILE_MAXLINESIZE):
            self._tickListForSave.clear()
            crntDateTime = datetime.datetime.now().strftime("%Y%m%d%H%M")
            self._tickFilePath = "./csv/" + self._tickFileName + "_" + str(crntDateTime) + "_" + self._coin + ".csv"


    def readTickList(self):
        df = pd.read_csv(self._tickFilePath)
        tmpList = df.values.tolist()
        for tick in tmpList:
            tmpTick = tick[1:]
            tmpTick[0] = int(tmpTick[0])
            self._tickList.append(tmpTick)
            self._convertTickDataToCandle(self._tickList)





if __name__ == '__main__':
    bitflyer = BitFlyerController()
    bitflyer.initGraph()

    bitsignal = BitSignalFinder(bitflyer._tickList, bitflyer._candleStats)

    index=0
    while(index<10):
        bitflyer.getTickData()
        stockstatsClass = bitflyer.convertToStockStats()
        print(bitflyer._tickList[-1])

        bitsignal.update(bitflyer._tickList, stockstatsClass)
        bitsignal.decideLossCut()

        bitsignal.buySignal()
        bitsignal.sellSignal()

        bitflyer.makeGraph(stockstatsClass)
        bitflyer.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
