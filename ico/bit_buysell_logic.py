import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats


from sklearn.preprocessing import MinMaxScaler


PARAM_OPEN = 0
PARAM_HIGH = 1
PARAM_LOW = 2
PARAM_CLOSE = 3
PARAM_VOLUME = 4

PARAM_MACD = 5
PARAM_MACDS = 6
PARAM_MACDH = 7
PARAM_RSI = 8
PARAM_BOLL = 9
PARAM_BOLL_UB = 10
PARAM_BOLL_LB = 11

#配列の一番最後が一番最新
TICK_NEWEST = -1


class BitSignalFinder():
    def __init__(self, tickDataList, stockstatClass, params=[]):

        if len(params) == 0:
            self._params = ['open', 'high', 'low', 'close', 'macd', 'macds', 'macdh', 'boll', 'boll_ub', 'boll_lb']
        else:
            self._params = params

        self.update(tickDataList, stockstatClass)

        # 買った際にincrement
        self._buyNum = 0
        self._buyPrice = 0

        self._sellPrice = 0

        self._scaler = MinMaxScaler(feature_range=(0, 1))

        # ボリンジャーバンドを下抜けた際の値段
        self._bollLBXPrice = 0
        # 最低額はboll_lb+3
        self._possibleSellPrice = 0
        # ボリンジャーバンドを下抜けた事がある
        self._hasLowerBollLb = False


    def update(self, tickDataList, stockstatClass):
        self._tickDataList = tickDataList
        self._stockstatClass = stockstatClass

        if(len(self._params) > 0):
            for param_ in self._params:
                self._stockstatClass.get(param_)


    def buySignal(self):
        macdAll = self._stockstatClass[:, PARAM_MACD]
        rsiAll = self._stockstatClass[:, PARAM_RSI]
        # print(macdAll)
        # print()
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]

        crntPrice = self._tickDataList[TICK_NEWEST][1]
        if(
            len(macdAll) > 3 and
            self._buyNum == 0 and

            #macd, rsiを使用
            # self._buyLogic_MACD()

            #ボリンジャーを用いた売りロジック
            self._buyLogic_Boll()
        ):

            #売ったことがある場合値段チェック。
            #現在の株価がsellよりも低くないとだめ
            if(self._sellPrice > 0 and crntPrice + 3 >= self._sellPrice):
                return False

            self._buyNum += 1
            if(float(crntPrice) > float(self._bollLBXPrice)):
                self._buyPrice = float(self._bollLBXPrice)
            else:
                self._buyPrice = crntPrice
            print("***Buy! {} price:{}, macd:{}, rsi:{}, self._sellPrice:{}".format(self._tickDataList[TICK_NEWEST][1], self._buyPrice, macdAll[TICK_NEWEST], rsiAll[TICK_NEWEST], self._sellPrice))
            return True

        return False



    def _buyLogic_Boll(self):
        bollAll = self._stockstatClass[:, PARAM_BOLL]
        bollUbAll = self._stockstatClass[:, PARAM_BOLL_UB]
        bollLbAll = self._stockstatClass[:, PARAM_BOLL_LB]
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]
        print("_buyLogic_Boll: hasLB:{}, aboveLB:{}, willX:{}".format(self._hasLowerBollLb, self.isAboveLowBoll(), self.willGoldenX()))
        if(
            #ボリンジャーLBが存在する
            math.isnan(bollLbAll[TICK_NEWEST]) == False and
            bollLbAll[TICK_NEWEST] > 0.0 and
            #ボリンジャーLBを下回った事がある。
            self._hasLowerBollLb and
            #今は上回っている
            self.isAboveLowBoll() and

            #ゴールデンクロスになる予兆
            self.willGoldenX() and

            # rsiに値が入っていること
            math.isnan(self._stockstatClass[:, PARAM_RSI][TICK_NEWEST]) == False and
            self._stockstatClass[:, PARAM_RSI][TICK_NEWEST] < 60.0 and
            # 高値の時は買わない
            scaledPrice < 0.2 and
            # 0に行くとさらに下がる可能性があるので
            scaledPrice > 0.05
        ):
            return True


    """
        ボリンジャーバンドLBを下抜けたかどうかの判断
        ロウソクの下ヒゲが当たったら_hasLowerBollLbをON
    """
    def isCrossingLowBolling(self):
        if(
            len(self._stockstatClass) > 3 and
            #ちゃんと値が入っていること
            math.isnan(self._stockstatClass[:, PARAM_BOLL_LB][TICK_NEWEST]) == False and
            self._stockstatClass[:, PARAM_BOLL_LB][TICK_NEWEST] > 0.0 and
            #ボリンジャーLB価格で比較
            self._stockstatClass[:, PARAM_LOW][TICK_NEWEST] < self._stockstatClass[:, PARAM_BOLL_LB][TICK_NEWEST] and
            #_hasLowerBollLbのフラグが立つのでRSIがセットされてない場合はスキップ
            self._stockstatClass[:, PARAM_LOW][TICK_NEWEST] > 0.0

        ):
            print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self._tickDataList[TICK_NEWEST][0], self._stockstatClass[:, PARAM_LOW][TICK_NEWEST], self._stockstatClass[:, PARAM_BOLL_LB][TICK_NEWEST]))
            self._bollLBXPrice = self._stockstatClass[:, PARAM_LOW][TICK_NEWEST]
            self._possibleSellPrice = self._bollLBXPrice + 3
            self._hasLowerBollLb = True
            return True
        return False



    """
        ボリンジャーバンドLBの上になったかの判断
    """
    def isAboveLowBoll(self):
        if(self._stockstatClass[:, PARAM_LOW][TICK_NEWEST] > self._stockstatClass[:, PARAM_BOLL_LB][TICK_NEWEST]):
            return True
        return False




    def isCrossingMidBolling(self):
        if(self._stockstatClass[:, PARAM_LOW][TICK_NEWEST] > self._stockstatClass[:, PARAM_BOLL][TICK_NEWEST]):
            return True
        return False


    def isCrossingHighBolling(self):
        if(self._stockstatClass[:, PARAM_HIGH][TICK_NEWEST] > self._stockstatClass[:, PARAM_BOLL_UB][TICK_NEWEST]):
            return True
        return False



    def isGoldenXed(self):
        if(self._stockstatClass[:, PARAM_MACD][TICK_NEWEST] > self._stockstatClass[:, PARAM_MACDS][TICK_NEWEST]):
            return True
        return False


    """
        ゴールデンクロス時にはもう遅い。
        差が大きく開いたところを狙う。
    """
    def willGoldenX(self):
        macdAll = self._stockstatClass[:, PARAM_MACD]
        macdsall = self._stockstatClass[:, PARAM_MACDS]
        macdDif1 = macdsall[TICK_NEWEST] - macdAll[TICK_NEWEST]
        macdDif2 = macdsall[-2] - macdAll[-2]
        macdDif3 = macdsall[-3] - macdAll[-3]

        # print("macdDiff:{}, {}, {}".format(macdDif1, macdDif2, macdDif3))
        if(macdDif1 > macdDif2 and macdDif2 > macdDif3):
            return True

        return False