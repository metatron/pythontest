import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats
import json
import os

from ico.bit_buysell_logic import BitSignalFinder

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
LBED_INTERVAL = 4

# GXしたかどうか
GOLDENXED_INTERVAL = 4



class SimpleSignalFinder(BitSignalFinder):


    def __init__(self, tickDataList, stockstatClass, extraFeeList, params=[]):
        super().__init__(tickDataList, stockstatClass, extraFeeList, params)

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




    def update(self, tickDataList, stockstatClass):
        self._tickDataList = tickDataList
        self._stockstatClass = stockstatClass

        self.lowAll = self._stockstatClass.get('low')
        self.crntLow = float(self.lowAll[TICK_NEWEST])

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

        if(self.crntTimeMin - self.startTimeMin > INITIAL_INTERVAL):
            self.canTrade = True


        self._checkGoldenXed_MacdS()
        self._buyLogic_Boll_GX()


    def buySignal(self, dryRun=True):
        print("buySignal {} canTrade:{}, buyPrice:{}, sellbuyflg:{}".format(self.crntTimeSec, self.canTrade, self._buyPrice, self._buySellSignalFlag))
        if (
            self.canTrade and
            self._buyPrice == 0 and
            self._buySellSignalFlag
        ):

            print("***Buy! {} price:{}, macd:{}, rsi:{}, goldedXedTime:{}".format(self.crntTimeSec, self.crntPrice, self.crntMacd, self.crntRsi, self._goldedXedTime))
            self._buyNum += 1
            self._buyPrice = self.crntPrice
            self._buyDateTime = self.crntTimeSec

            return self._buyPrice
        return 0


    def _buyLogic_Boll_GX(self):
        # パラメータ更新があるのでとりあえず実行。結果を取得
        xedLB = self.checkCrossingLowBollingInterval()
        gXed = self.checkGoldenXedInterval()

        # print("_buyLogic_Boll_GX {}: xedLB:{}, gXed:{}, rsi: {}".format(self.crntTimeSec, xedLB, gXed, self.crntRsi))

        if(
            #ボリンジャーLBを下回った事がある。
            xedLB and
            #今は上回っている
            self.isAboveLowBoll() and

            #ゴールデンクロス発生中
            gXed and

            # rsiに値が入っていること
            self.crntRsi <= 40.0 and
            self.crntRsi > 0.0
        ):
            self._buySellSignalFlag = True
            return True
        return False



    """
        ゴールデンクロスチェック（MacdH(grey)とMacdS(yellow)使用）
        時間更新
        
        updateで使用
    """
    def _checkGoldenXed_MacdS(self):
        # print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(crntTime, (allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdS[-2] - allMacdH[-2])))

        if (
            self._goldedXedTime == 0 and
            # macdの一番最新は確実に上回っている事
            self.crntMacdH - self.crntMacdS > 0 and
            # 2番目はMacdSが低い
            self.macdHAll[-2] - self.macdSAll[-2] < 0
        ):
            print("goldedXedTime ON! {} macd1:{}, macd2:{}".format(self.crntTimeSec, (self.crntMacdH - self.crntMacdS), (self.macdHAll[-2] - self.macdSAll[-2])))
            self._goldedXedTime = self.crntTimeMin



    """
        ゴールデンクロスが起こったら一定期間ONにする。
        4足目まで継続。
    """
    def checkGoldenXedInterval(self):
        # クロスした
        if(self._goldedXedTime > 0):
            # クロス期間内
            if((self.crntTimeMin - self._goldedXedTime) <= GOLDENXED_INTERVAL):
                return True
            else:
                print("goldedXedTime OFF! {}".format(self.crntTimeSec))
                self._goldedXedTime = 0

        return False




    """
        バンドLBを下抜けたかどうかの判断
        ロウソクの下ヒゲが当たったら _hasLowerBollLb をON
    """
    def checkCrossingLowBollingInterval(self):
        if(
            # Lbの期間がすぎた
            self._lowerBollLbTime == 0 and

            #がちゃんとした値であること
            self.crntBollLb > 0.0 and
            self.crntLow > 0.0 and

            #ボリンジャーLB価格で比較
            self.crntLow < self.crntBollLb and

            #下抜け期間である
            (
                self._lowerBollLbTime == 0 or
                self.crntTimeMin - self._lowerBollLbTime <= LBED_INTERVAL
            )
        ):
            print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self.crntTimeSec, self.crntLow, self.crntBollLb))
            self._lowerBollLbTime = self.crntTimeMin


        if(self._lowerBollLbTime > 0):
            if(self.crntTimeMin - self._lowerBollLbTime > LBED_INTERVAL):
                print("Crossed LB RESET!: time:{}, low:{}, boll_lb:{},".format(self.crntTimeSec, self.crntLow, self.crntBollLb))
                self._lowerBollLbTime = 0
                return False
            else:
                return True

        return False





    def sellSignal(self, dryRun=True):
        if(
            self.canTrade and
            self._buyNum > 0.0 and

            # 売買フラグがON
            self._buySellSignalFlag and
            self._buyPrice > 0 and
            self.crntPrice > self._buyPrice + 1.0
        ):
            self._buyNum -= 1
            self._sellPrice = self.crntPrice
            #利益算出
            earnedVal = self._sellPrice - self._buyPrice
            self._totalEarned += earnedVal
            print("***Sell! {} price:{}, macd:{}, rsi:{}, totalEarned:{}".format(self.crntTimeSec, self._sellPrice, self.crntMacd, self.crntRsi, self._totalEarned))

            # Buyを行う為のリセット
            self.resetParamsForBuy()

            return self._sellPrice

        return 0



    """
        デッドクロスチェック（MacdH(grey)とMacdS(yellow)使用）
        時間更新

        updateで使用
    """

    def _checkDeadXed_MacdS(self):
        # print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(crntTime, (allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdS[-2] - allMacdH[-2])))

        if (
            self.canTrade and
            (
                self._goldedXedTime > 0 and
                # 最新のmacdHがSよりも低い
                self.crntMacdH - self.crntMacdS < 0 and
                # 前回はmacdHが高い
                self.macdHAll[-2] - self.macdSAll[-2] > 0
            ) or
            (
                # 3回連続macdH下落
                self.crntMacdH < self.macdHAll[-2] and self.macdHAll[-2] < self.macdHAll[-3]
            )
        ):
            print(
                "_checkDeadXed_MacdS {} macd1:{}, macd2:{}".format(self.crntTimeSec, (self.crntMacdH - self.crntMacdS),
                                                                    (self.macdHAll[-2] - self.macdSAll[-2])))
            self._goldedXedTime = 0
            self._buySellSignalFlag = False
            self._buyPrice = 0
            self._sellPrice = 0
            self._lowerBollLbTime = 0


    """
        再びBuyを行う為のリセット
    """
    def resetParamsForBuy(self):
        self._buyPrice = 0
        self._sellPrice = 0

        self._deleteStatus()