import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats
import json
import os
import datetime
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt



PARAM_OPEN = 0
PARAM_HIGH = 1
PARAM_LOW = 2
PARAM_CLOSE = 3
PARAM_VOLUME = 4

# 配列の一番最後が一番最新
TICK_NEWEST = -1

TICK_PARAM_DATETIME = 0
TICK_PARAM_PRICE = 1

# 取引開始後何分かは売買しない
INITIAL_INTERVAL = 3

# バンドが下抜けてからの有効期間（分）
LBED_INTERVAL = 5

# GXしたかどうか
GOLDENXED_INTERVAL = 4

# ロスカチェックの入るタイミング（購入してからの時間（分））
LOSSCUT_STARTTIMING_INERVAL = 5

# ロウソク足の種類
CANDLETYPE_POS = 0
CANDLETYPE_NEG = 1

# ガラッたタイムのリセットタイミング
SUDDENDROP_RESET_INERVAL = 4
#10上記期間のうち10回も怒ったら即売り
SUDDENDROP_LOSSCUT_NUM = 10

#売った直後は買わない。これ分だけ待つ
NEXT_BUY_WAIT_TIME = 1

#近似曲線を得る為に必要な値段のリスト（約3分間）
NEED_COUNT_FOR_APPROXIMATION = 5

#買ってから何分たったか。
BOUGHT_INTERVAL = 3

#買う際若干高くする
INCREMENTED_BUYPRICE = 0.8

#status save
STATUS_FILEPATH = './status.json'



def linear_fit(x, a, b):
    return a * x + b


class ScalpingLogic():

    def __init__(self, tickDataList, stockstatClass, extraFeeList, params=[]):
        self.crntPrice = 0
        self.crntTimeSec = 0
        self.crntTimeMin = 0
        self.startTimeMin = 0

        self.macdAll = None
        self.macdHAll = None
        self.macdSAll = None
        self.bollUbAll = None
        self.bollLbAll = None
        self.rsiAll = None

        # あまりに早くトレードしはじめると危険（値がないから）
        self.canTrade = False

        # 売買フラグ。これがONの場合売買する。
        self._buySellSignalFlag = False

        # 理想の売り値（既に定義済み）
        # self._possibleSellPrice = 0

        # 通知中かどうか
        self._waitingForRequest = False

        # 急激な寝落ちが起きた時間
        self.suddenDropTimeMin = 0
        self.suddenDropNum = 0

        # 最後に買った時のRsi保持。これ以上高くないと買わない。sellでリセット。
        self.prevBoughtRsi = 0

        # これ以上高くは買わない
        self.maxBuyPrice = 0

        #売った時間
        #この時に買いは走らないようにする。売ったということは下がる確率が高い。
        self.soldTimeMin = 0

        # 連続でbuyNum > sellNumの回数
        self.buyTrigger = False
        self._buyPrice = 0
        self.sellTrigger = False
        self._sellPrice = 0

        self._buyDateTime = 0

        # トリガーした際の値段（これよりも200円高かったら買わない）
        self.triggeredPrice = 0

        # 近似値グラフ用
        self._graphXNumpyList = []
        self.kinjiAB = [0,0]

        self.netEarned = 0






    def update(self, tickDataList, stockstatClass):
        self._tickDataList = tickDataList
        self._stockstatClass = stockstatClass

        self.openAll = self._stockstatClass.get('open')
        self.crntOpen = float(self.openAll[TICK_NEWEST])

        self.highAll = self._stockstatClass.get('high')
        self.crntHigh = float(self.highAll[TICK_NEWEST])

        self.lowAll = self._stockstatClass.get('low')
        self.crntLow = float(self.lowAll[TICK_NEWEST])

        self.closeAll = self._stockstatClass.get('close')
        self.crntClose = float(self.closeAll[TICK_NEWEST])

        self.macdAll = self._stockstatClass.get('macd')   # orange
        self.crntMacd = float(self.macdAll[TICK_NEWEST])

        self.macdHAll = self._stockstatClass.get('macdh') # grey
        self.crntMacdH = float(self.macdHAll[TICK_NEWEST])

        self.macdSAll = self._stockstatClass.get('macds') # yellow
        self.crntMacdS = float(self.macdSAll[TICK_NEWEST])

        self.rsiAll = self._stockstatClass.get('rsi_12')
        self.crntRsi = float(self.rsiAll[TICK_NEWEST])

        self.bollUbAll = self._stockstatClass.get('boll_ub')
        self.crntBollUb = float(self.bollUbAll[TICK_NEWEST])

        self.bollLbAll = self._stockstatClass.get('boll_lb')
        self.crntBollLb = float(self.bollLbAll[TICK_NEWEST])

        self.prevPrice = float(self.crntPrice)

        self.crntPrice = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE])
        self.crntTimeSec = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME])
        self.crntTimeMin = int(str(self.crntTimeSec)[:12])

        if(self.startTimeMin == 0):
            self.startTimeMin = self.crntTimeMin

        _diff = self._timeMinDiff(self.crntTimeMin, self.startTimeMin)
        if(_diff > INITIAL_INTERVAL):
            self.canTrade = True


    def getBuyInfo(self, executionList):
        if(len(executionList) == 0):
            return [0, 0, 0, 0]

        buyPriceList = []
        buyNum = 0
        sellNum = 0
        for data in executionList:
            if(data['taker_side'] == "sell"):
                sellNum += 1
            else:
                buyNum += 1
                buyPriceList.append(float(data['price']))

        buyPercent = math.fabs(buyNum/len(executionList))

        indexList = [float(i) for i in range(len(buyPriceList))]

        if(len(indexList) != len(buyPriceList)):
            return [buyNum, sellNum, 0, buyPercent]

        #グラフ用に保存
        self._graphXNumpyList = np.array(buyPriceList)

        param = [0, 0]
        try:
            param, cov = curve_fit(linear_fit, np.array(indexList), np.array(buyPriceList))
        except Exception as e:
            print(str(e))

        self.kinjiAB[0] = param[0] # a
        self.kinjiAB[1] = param[1] # b

        return [buyNum, sellNum, self.kinjiAB[0], buyPercent]




    def checkBuyInfo(self, buyNum, sellNum, aVec, buyPercent):
        if(self._buySellSignalFlag):
            return False

        # 20人以上が参加していなかったらシカト
        if(buyNum + sellNum < 10):
            return False

        if(self._sellPrice > 0):
            return False

        if (
            self.buyTrigger == False and
            buyNum < sellNum and
            aVec < 0 and
            buyPercent < 0.5
        ):
            print("*****buy triggered!")
            self.buyTrigger = True
            self.triggeredPrice = self.crntPrice

        # 2段階認証。buyNumが回復した瞬間にBuy
        if(
            self.buyTrigger == True and
            buyNum > sellNum and
            self.crntPrice > self.prevPrice
            # aVec > 0
        ):
            print("*****buy!")
            self._buySellSignalFlag = True
            self._buyPrice = self.crntPrice + INCREMENTED_BUYPRICE #ちょい高く買うことで買いやすくする
            self.triggeredPrice = 0
            self._buyDateTime = self.crntTimeMin
            return True

        return False





    def checkSellInfo(self, buyNum, sellNum, aVec, buyPercent):
        if(self._buySellSignalFlag == False):
            return False

        if(self._buyPrice <= 0):
            return False


        # 時間が立ちすぎていたら即売り
        if(
            self._timeMinDiff(self.crntTimeMin, self._buyDateTime) >= BOUGHT_INTERVAL and
            self.crntPrice > self._buyPrice
        ):
            print("*****sell by timeout!")
            self.buyTrigger = False
            self._buySellSignalFlag = False
            self.sellTrigger = False

            self.netEarned += (self.crntPrice - self._buyPrice)
            print("**Diff:{}".format(self.crntPrice - self._buyPrice))
            self._buyPrice = 0
            self._sellPrice = self.crntPrice

            return True


        if(
            self.sellTrigger == False and
            self.crntPrice > self._buyPrice and
            buyNum > sellNum and
            aVec > 0
        ):
            print("*****sell triggered!")
            self.sellTrigger = True


        # 2段階認証
        if(
            self.sellTrigger == True and
            self.crntPrice > self._buyPrice and
            (aVec < 0 or buyNum < sellNum)
        ):
            print("*****sell!")
            self.buyTrigger = False
            self._buySellSignalFlag = False

            self.sellTrigger = False

            self.netEarned += (self.crntPrice - self._buyPrice)
            print("**Diff:{}".format(self.crntPrice - self._buyPrice))
            self._buyPrice = 0
            self._sellPrice = self.crntPrice

            return True

        return False


    def checkCancelInfo(self, buyNum, sellNum, aVec, buyPercent):
        if(buyNum < sellNum):
            print("checkCancelInfo: buyNum:{} < sellNum:{}".format(buyNum, sellNum))
            return True

        # 若干高く買ってるのでそのその分を引いて確認
        if(self.crntPrice < (self._buyPrice - INCREMENTED_BUYPRICE)):
            print("checkCancelInfo: crntPrice:{} < _buyPrice:{}".format(self.crntPrice, self._buyPrice))
            return True

        return False


    def getUpdatedPrice(self):
        if(self._buySellSignalFlag == False):
            return 0

        if(self._buyPrice <= 0):
            return 0

        self._buyPrice = self.crntPrice + INCREMENTED_BUYPRICE
        return self._buyPrice


    def updateStatus(self, side, orderId):
        if(side=="buy"):
            self._buyOrderId = str(orderId)
            self._sellOrderId = ""
            # self._saveStatus()
        elif (side == "sell"):
            self._sellOrderId = str(orderId)
            self._buyOrderId = ""
            # self._saveStatus()









    """
        再びBuyを行う為のリセット
    """
    def resetParamsForBuy(self):
        self._buyPrice = 0
        self._sellPrice = 0
        self._possibleSellPrice = 0
        self.prevBoughtRsi = 0

        self._buySellSignalFlag = False
        self.buyTrigger = False
        self.sellTrigger = False

        # self._deleteStatus()


    """
        時間（日時分）の時間差を分で返す。
        
        :return float 差分(分）
    """
    def _timeMinDiff(self, crntTimeMin, prevTimeMin):
        _crntTime = self._intToDateTimeMin(crntTimeMin)
        _prevTime = self._intToDateTimeMin(prevTimeMin)

        delta = _crntTime - _prevTime
        return float(delta.total_seconds()/60.0)


    def _intToDateTimeMin(self, crntTimeMin):
        yr = int(str(crntTimeMin)[0:4])
        mt = int(str(crntTimeMin)[4:6])
        dt = int(str(crntTimeMin)[6:8])
        tm = int(str(crntTimeMin)[8:10])
        mn = int(str(crntTimeMin)[10:12])

        return datetime.datetime(yr, mt, dt, tm, mn)


    """
        通信中フラグON
    """
    def getWaitingForRequest(self):
        return self._waitingForRequest

    """
        通信中フラグOFF
    """
    def setWaitingForRequest(self, status):
        self._waitingForRequest = status


    def plotToKinjichi(self):
        # plot graph
        fig = plt.figure(figsize=(10, 5))
        plt.title('Stock Graph', fontsize=8)

        #一つ目
        ax1 = fig.add_subplot(1,1,1)
        indexList = [float(i) for i in range(len(self._graphXNumpyList))]
        ax1.scatter(np.array(indexList), self._graphXNumpyList, color='red')

        yList = [linear_fit(x, self.kinjiAB[0], self.kinjiAB[1]) for x in indexList]
        ax1.plot(np.array(yList), color='blue', linestyle='dashed')

        if (os.path.exists("./figures") != True):
            os.mkdir("./figures")

        plt.savefig("./figures/candle.jpg", format="jpg", dpi=120)

