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

        self._buySignalFlag = False




    def update(self, tickDataList, stockstatClass):
        self._tickDataList = tickDataList
        self._stockstatClass = stockstatClass

        self.lowAll = self._stockstatClass.get('low')
        self.crntLow = self.lowAll[TICK_NEWEST]

        self.macdAll = self._stockstatClass.get('macd')   # orange
        self.crntMacd = self.macdAll[TICK_NEWEST]

        self.macdHAll = self._stockstatClass.get('macdh') # grey
        self.crntMacdH = self.macdHAll[TICK_NEWEST]

        self.macdSAll = self._stockstatClass.get('macds') # yellow
        self.crntMacdS = self.macdSAll[TICK_NEWEST]

        self.rsiAll = self._stockstatClass.get('rsi_12')
        self.crntRsi = self.rsiAll[TICK_NEWEST]

        self.bollUbAll = self._stockstatClass.get('boll_ub')
        self.crntBollUb = self.bollUbAll[TICK_NEWEST]

        self.bollLbAll = self._stockstatClass.get('boll_lb')
        self.crntBollLb = self.bollLbAll[TICK_NEWEST]

        self.prevPrice = self.crntPrice

        self.crntPrice = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE])
        self.crntTimeSec = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME])
        self.crntTimeMin = int(str(self.crntTimeSec)[:12])

        if(self.startTimeMin == 0):
            self.startTimeMin = self.crntTimeMin

        if(self.crntTimeMin - self.startTimeMin > INITIAL_INTERVAL):
            self.canTrade = True

        self._checkGoldenXed_MacdS()


    def buySignal(self, dryRun=True):
        pass



    def _buyLogic_Boll_GX(self):
        if(
            #ボリンジャーLBを下回った事がある。
            self.checkCrossingLowBollingInterval() and
            #今は上回っている
            self.isAboveLowBoll() and

            #ゴールデンクロス発生中
            self.checkGoldenXedInterval() and

            # rsiに値が入っていること
            self.crntRsi < 60.0
        ):
            print("***Buy logic:[_buyLogic_Boll_GX] True")
            return True
        return False



    """
        ゴールデンクロスチェック（MacdH(grey)とMacdS(yellow)使用）
        時間、フラグ更新
        最初反応がmacdhを使用していたが、反応が早すぎる事がある。macdとmacdsに変更。
        TICK_NEWESTはアップダウンが激しいため-2,-3で比較
        
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
            print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(self.crntTimeSec, (self.crntMacdH - self.crntMacdS), (self.macdHAll[-2] - self.macdSAll[-2])))
            self._goldedXedTime = self.crntTimeMin



    """
        ゴールデンクロス期間かどうか
        4足目まで継続
    """
    def checkGoldenXedInterval(self):
        # クロスした
        if(self._goldedXedTime > 0):
            # クロス期間内
            if((self.crntTimeMin - self._goldedXedTime) <= GOLDENXED_INTERVAL):
                return True

        else:
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
            return True


        if(self._lowerBollLbTime > 0 and self.crntTimeMin - self._lowerBollLbTime > LBED_INTERVAL):
            print("Crossed LB RESET!: time:{}, low:{}, boll_lb:{},".format(self.crntTimeSec, self.crntLow, self.crntBollLb))
            self._lowerBollLbTime = 0

        return False






    def sellSignal(self, dryRun=True):
        pass