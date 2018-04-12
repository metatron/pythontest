import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats
import json
import os
import datetime

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
LBED_INTERVAL = 5

# GXしたかどうか
GOLDENXED_INTERVAL = 4

# ロスカチェックの入るタイミング（購入してからの時間（分））
LOSSCUT_STARTTIMING_INERVAL = 10

# ロウソク足の種類
CANDLETYPE_POS = 0
CANDLETYPE_NEG = 1

# ガラッたタイムのリセットタイミング
SUDDENDROP_RESET_INERVAL = 4
#10上記期間のうち10回も怒ったら即売り
SUDDENDROP_LOSSCUT_NUM = 10

#売った直後は買わない。これ分だけ待つ
NEXT_BUY_WAIT_TIME = 1

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


        self._checkGoldenXed_MacdS()
        self._checkGoldenXed_Macd() #上で検知できなかった場合有用
        self._buyLogic_Boll_GX()


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

            # 売った時は買わない。既に高値の可能性が高い
            self.crntTimeMin - self.soldTimeMin >= NEXT_BUY_WAIT_TIME
        ):

            print("***Buy! {} price:{}, macd:{}, rsi:{}, goldedXedTime:{}".format(self.crntTimeSec, self.crntPrice, self.crntMacd, self.crntRsi, self._goldedXedTime))
            self._buyNum += 1
            self._buyPrice = self.crntPrice
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

        # print("_buyLogic_Boll_GX {}: xedLB:{}, gXed:{}, isAbove:{}, rsi:{}".format(self.crntTimeSec, xedLB, gXed, self.isAboveLowBoll(), self.crntRsi))

        if(
            # #ボリンジャーLBを下回った事がある。
            # xedLB and
            #今は上回っている
            self.isAboveLowBoll() and

            #ゴールデンクロス発生中
            gXed and

            # ガラがない
            dropped == False and

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
        ゴールデンクロスチェック（macd(orange)とMacdS(yellow)使用）
        時間更新

        updateで使用
    """

    def _checkGoldenXed_Macd(self):
        # print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(crntTime, (allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdS[-2] - allMacdH[-2])))

        if (
                self._goldedXedTime == 0 and
                # macdの一番最新は確実に上回っている事
                self.crntMacd - self.crntMacdS > 0 and
                # 2番目はMacdSが低い
                self.macdAll[-2] - self.macdSAll[-2] < 0
        ):
            print("goldedXedTime ON! (2nd) {} macd1:{}, macd2:{}".format(self.crntTimeSec, (self.crntMacdH - self.crntMacdS),
                                                                   (self.macdHAll[-2] - self.macdSAll[-2])))
            self._goldedXedTime = self.crntTimeMin


    """
        ゴールデンクロスが起こったら一定期間ONにする。
        4足目まで継続。
    """
    def checkGoldenXedInterval(self):
        # クロスした
        if(self._goldedXedTime > 0):
            diff = self._timeMinDiff(self.crntTimeMin, self._goldedXedTime)
            # クロス期間内
            if(diff <= GOLDENXED_INTERVAL):
                return True
            else:
                print("goldedXedTime OFF! crntTimeMin:{}, _goldedXedTime:{}, diff:{}".format(self.crntTimeMin, self._goldedXedTime, diff))
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
                self._timeMinDiff(self.crntTimeMin, self._lowerBollLbTime) <= LBED_INTERVAL
            )
        ):
            print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self.crntTimeSec, self.crntLow, self.crntBollLb))
            self._lowerBollLbTime = self.crntTimeMin


        if(self._lowerBollLbTime > 0):
            if(self._timeMinDiff(self.crntTimeMin, self._lowerBollLbTime) > LBED_INTERVAL):
                print("Crossed LB RESET!: time:{}, low:{}, boll_lb:{},".format(self.crntTimeSec, self.crntLow, self.crntBollLb))
                self._lowerBollLbTime = 0
                return False
            else:
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
        デッドクロスチェック（MacdH(grey)とMacdS(yellow)使用）
        ここでフラグを操作するとGXが起こるまでしばらく買えないので注意。

        updateで使用
    """

    def _checkDeadXed_MacdS(self):
        # if(len(self.macdHAll) > 3):
        #     print("_checkDeadXed_MacdS {} canTrade:{}, _buySellSignalFlag:{}, _buyPrice:{}, macdDiff:{}".format(self.crntTimeSec, self.canTrade, self._buySellSignalFlag, self._buyPrice, (self.crntMacdH < self.macdHAll[-2] and self.macdHAll[-2] < self.macdHAll[-3])))

        if (
            self.canTrade and
            len(self.macdHAll) > 3 and
            self._buySellSignalFlag and
            # (
            #     len(self.macdHAll) > 3 and
            #     self._goldedXedTime > 0 and
            #     # 最新のmacdHがSよりも低い
            #     self.crntMacdH - self.crntMacdS < 0 and
            #     # 前回はmacdHが高い
            #     self.macdHAll[-2] - self.macdSAll[-2] > 0
            # ) or
            (
                # 3回連続macdH下落
                self.crntMacdH < self.macdHAll[-2] and self.macdHAll[-2] < self.macdHAll[-3]
            )
            or
            (
                #ガラの際は買わない
                # self.suddenDropTimeMin > 0
            )
            ):
            print("_checkDeadXed_MacdS!! {} buyPrice:{}, macdDiff:{}".format(
                self.crntTimeSec, self._buyPrice,
                (self.crntMacdH < self.macdHAll[-2] and self.macdHAll[-2] < self.macdHAll[-3])))

            self._goldedXedTime = 0
            self._buySellSignalFlag = False
            self._lowerBollLbTime = 0
            #理想売値を修正（1円でもたかかったら即売り）
            self._possibleSellPrice = self._buyPrice + 1.0
            #Sellする特に規制しない
            # self._buyPrice = 0
            # self._sellPrice = 0


    """
        大量ガラした
        一定時間たったら即復帰させたいので
        _checkDeadXed_MacdSには追加しない。
    """
    def checkSupriseDrop(self):
        if(
            (self.crntPrice > 0 and self.crntOpen > 0) and
            self.crntPrice - self.crntOpen < -2100.0
        ):
            print("checkSupriseDrop!! {} self.crntPrice:{}, self.crntOpen:{}, diff:{}".format(self.crntTimeSec, self.crntPrice, self.crntOpen, (self.crntPrice - self.crntOpen)))
            self.suddenDropTimeMin = self.crntTimeMin
            self.suddenDropNum += 1
            return True

        #タイムがセットされている場合は時間をみてリセットする
        if(self.suddenDropTimeMin > 0):
            # 一定時間たったらリセット
            if(self._timeMinDiff(self.crntTimeMin, self.suddenDropTimeMin) > SUDDENDROP_RESET_INERVAL):
                print("checkSupriseDrop RESET!! {} self.crntPrice:{}, interval:{}".format(self.crntTimeSec, self.crntPrice,self._timeMinDiff(self.crntTimeMin, self.suddenDropTimeMin)))
                self.suddenDropTimeMin = 0
                self.suddenDropNum = 0
                return False
        # タイムがセットされていない
        else:
            return False

        return True



    """
        一定時間たっても売れない場合はロスカ
    """
    def lossCutSell(self):
        if(self.getWaitingForRequest()):
            return 0

        if(
            # 買ったことがある
            self._buyPrice > 0 and
            self._possibleSellPrice > 0 and
            #まだ売りが走ってない
            self._sellPrice == 0 and
            # 一定時間経過した
            self._timeMinDiff(self.crntTimeMin, self._buyDateTime) >= LOSSCUT_STARTTIMING_INERVAL and
            (
                # 買いよりは高いが理想値段になっていない
                (self.crntPrice > self._buyPrice and self._possibleSellPrice > self.crntPrice)
                or
                #ガラがきた
                (
                    self.suddenDropTimeMin > 0 and
                    self.suddenDropNum >= SUDDENDROP_LOSSCUT_NUM
                )
            )
        ):
            self._buyNum -= 1
            self._sellPrice = self.crntPrice
            #利益算出
            earnedVal = self._sellPrice - self._buyPrice
            self._totalEarned += earnedVal
            print("***lossCutSell! {} price:{}, macd:{}, rsi:{}, totalEarned:{}".format(self.crntTimeSec, self._sellPrice, self.crntMacd, self.crntRsi, self._totalEarned))

            return self._sellPrice

        return 0



    def getCandleType(self, timePrev=TICK_NEWEST):
        if(len(self.highAll) < 3):
            return CANDLETYPE_NEG

        # 現在のロウソクはまだできてないのでTickデータを使用
        if(timePrev == TICK_NEWEST):
            if(self.crntPrice - self.crntLow > 0):
                return CANDLETYPE_POS
            return CANDLETYPE_NEG

        # ロウソクができていればそれを使用
        if(self.highAll[timePrev] > self.lowAll[timePrev]):
            return CANDLETYPE_POS
        return CANDLETYPE_NEG



    """
        再びBuyを行う為のリセット
    """
    def resetParamsForBuy(self):
        self._buyPrice = 0
        self._sellPrice = 0
        self._possibleSellPrice = 0
        self.prevBoughtRsi = 0

        self._deleteStatus()


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



#TODO 負けない実装
#売値の選定
#過去の最高値よりも高くは設定しない。
#陽線のcloseを設定

#self.prevBoughtRsiが効いてない