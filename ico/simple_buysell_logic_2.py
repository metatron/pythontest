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

from ico.simple_buysell_logic import SimpleSignalFinder

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
NEED_COUNT_FOR_APPROXIMATION = 180


def linear_fit(x, a, b):
    return a * x + b


class SimpleSignalFinder2(SimpleSignalFinder):


    def __init__(self, tickDataList, stockstatClass, extraFeeList, params=[]):
        super().__init__(tickDataList, stockstatClass, extraFeeList, params)






    def buySignal(self, dryRun=True):
        if(self.getWaitingForRequest()):
            return 0

        print("buySignal {} canTrade:{}, crntPrice:{}, buyPrice:{}, sellbuyflg:{}, rsi:{}, candle:{}".format(self.crntTimeSec, self.canTrade, self.crntPrice, self._buyPrice, self._buySellSignalFlag, self.crntRsi, self.getCandleType()))
        if (
            self.canTrade and
            self._buyPrice == 0 and
            self._buySellSignalFlag and

            #連続買いする時はRsiが前回よりも高くないとダメ
            self.crntRsi > self.prevBoughtRsi and

            # rsiが下記以下で連続買いが走る。
            self.crntRsi <= 60.0 and
            self.crntRsi > 0.0 and

            # 陽線の時に買う
            self.getCandleType() == CANDLETYPE_POS and

            # 売った時の分足では買わない。既に高値の可能性が高い
            self.crntTimeMin - self.soldTimeMin >= NEXT_BUY_WAIT_TIME
        ):

            print("***Buy! {} price:{}, macd:{}, rsi:{}, goldedXedTime:{}".format(self.crntTimeSec, self.crntPrice, self.crntMacd, self.crntRsi, self._goldedXedTime))
            self._buyNum += 1
            self._buyPrice = self.crntPrice + 0.5 #0.5円高く買うことで買いやすくする。
            self._buyDateTime = self.crntTimeSec
            self.prevBoughtRsi = self.crntRsi
            self.soldTimeMin = 0

            # ロスカ、売りで使用
            self._possibleSellPrice = self.getMinSellPrice(self._buyPrice, coinAmount=self._coinAmount, minEarn=self._minEarn)[0]

            return self._buyPrice
        return 0



    """
        BuySellフラグをONにする。
        これがONだとBuyが走る
    """
    def _buyLogic_Boll_GX(self):
        # パラメータ更新があるのでとりあえず実行。結果を取得
        xedLB = self.checkCrossingLowBollingInterval()
        gXed = self.checkGoldenXedInterval()
        dropped = self.checkSupriseDrop()

        if (len(self._tickDataList) < NEED_COUNT_FOR_APPROXIMATION):
            return False

        priceList = [self._tickDataList[i][1] for i in range(len(self._tickDataList))]
        indexList = [float(i) for i in range(len(self._tickDataList))]
        #後ろから300件取得
        priceList = priceList[-NEED_COUNT_FOR_APPROXIMATION:]
        indexList = indexList[-NEED_COUNT_FOR_APPROXIMATION:]

        param, cov = curve_fit(linear_fit, np.array(indexList), np.array(priceList))
        a = param[0]
        b = param[1]

        # print("_buyLogic_Boll_GX {}: xedLB:{}, gXed:{}, isAbove:{}, rsi:{}".format(self.crntTimeSec, xedLB, gXed, self.isAboveLowBoll(), self.crntRsi))
        print("_buyLogic_Boll_GX {}:, a:{}, crntPrice: {}".format(self.crntTimeSec, a, self.crntPrice))

        if(
            # #ボリンジャーLBを下回った事がある。
            # xedLB and
            #今は上回っている
            # self.isAboveLowBoll() and

            #ゴールデンクロス発生中
            # gXed and

            # ガラがない
            # dropped == False and

            a > 1.0 and

            # rsiに値が入っていること
            self.crntRsi <= 60.0 and
            self.crntRsi > 0.0
        ):
            self._buySellSignalFlag = True
            return True
        return False





    def sellSignal(self, dryRun=True):
        if(self.getWaitingForRequest()):
            return 0

        if(
            self.canTrade and
            self._buyNum > 0.0 and

            # 売買フラグがON
            # self._buySellSignalFlag and
            self._buyPrice > 0 and
            self.crntPrice > self._possibleSellPrice
        ):
            self._buyNum -= 1
            self._sellPrice = self.crntPrice
            #利益算出
            earnedVal = self._sellPrice - self._buyPrice
            self._totalEarned += earnedVal
            print("***Sell! {} sell:{}, bought:{}, macd:{}, rsi:{}, totalEarned:{}".format(self.crntTimeSec, self._sellPrice, self._buyPrice, self.crntMacd, self.crntRsi, self._totalEarned))

            self.soldTimeMin = self.crntTimeMin

            # Buyを行う為のリセット
            # self.resetParamsForBuy()

            return self._sellPrice

        return 0



    """
    買った金額、個数から「利益額」を出す為に0.001コインあたりいくらでうればいいかを算出
    :param minEarn 売らなければならないコインを全て売った時の利益額

    return: [1コイン辺りの最低売り金額, 買いの時との差, 売らなければいけないコイン個数] 
    """
    def getMinSellPrice(self, buyPrice, coinAmount=0.001, minEarn=1.0):
        # 買ったコインを円に変換
        actualBuyYenPrice = buyPrice * coinAmount
        # 売り（円）を設定
        idealSellYenPrice = actualBuyYenPrice + minEarn
        # 売りのコイン値に変換
        idealSellPrice = idealSellYenPrice / coinAmount

        diffPrice = idealSellPrice - buyPrice

        return [idealSellPrice, diffPrice, coinAmount]



# 近似曲線
# https://qiita.com/hik0107/items/9bdc236600635a0e61e8

#近似曲線にぶち込む
#微分して傾きを算出。