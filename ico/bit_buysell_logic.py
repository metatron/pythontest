import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats
import json
import os


from sklearn.preprocessing import MinMaxScaler
from statistics import mean

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

TICK_PARAM_DATETIME = 0
TICK_PARAM_PRICE = 1

# LB下抜けしてから下記分間は下抜け時間
LBED_INTERVAL = 15

# ゴールデンXから下記分間はXした時間
GOLDENXED_INTERVAL = 4

# ロウソク足の種類
CANDLETYPE_POS = 0
CANDLETYPE_NEG = 1

# 500以上上昇
SUDDEN_PRICE_UP = 600
SUDDEN_PRICE_UP_INTERVAL = 3

#ロスカットファイナル
LOSSCUT_FINAL_TIMEINTERVAL = 2*60

#status save
STATUS_FILEPATH = './status.json'


class BitSignalFinder():
    def __init__(self, tickDataList, stockstatClass, extraFeeList, params=[]):

        if len(params) == 0:
            self._params = ['open', 'high', 'low', 'close', 'macd', 'macds', 'macdh', 'rsi_9', 'boll', 'boll_ub', 'boll_lb']
        else:
            self._params = params

        self._scaler = MinMaxScaler(feature_range=(0, 1))

        # 買った際にincrement
        self._buyNum = 0

        # 一番最後に買った時の値段
        self._buyPrice = 0
        self._buyDateTime = None

        # 取引所で買った際のID
        self._buyOrderId = ""

        # 一番最後に売った時の値段
        self._sellPrice = 0

        # 取引所で売った際のID
        self._sellOrderId = ""


        #コイン個数（ディフォルト0.001）
        self._coinAmount = 0.001

        #最低利益額（全coinAmount個ぶん売った時手数料をのぞいた最低利益額。円）
        self._minEarn = 1.0

        #手数料 ex) [0.0015, 0.0014]
        self._extraFeeList = extraFeeList

        # トータル利益
        self._totalEarned = 0.0

        # ボリンジャーバンドを下抜けた際の値段
        self._bollLBXPrice = 0
        # 最低額はboll_lb+3
        self._possibleSellPrice = 0
        # ボリンジャーバンドを下抜けた事がある
        self._hasLowerBollLb = False
        self._lowerBollLbTime = 0 #分

        # ゴールデンクロスになった事がある
        self._isGoldedXed = False
        self._goldedXedTime = 0

        # バンドを上抜けた事がある
        self._hasBollUbed = False
        self._bollUbedTime = 0
        self._bollUbedInterval = 0

        #上をタッチした回数
        self._bollUbedNum = 0
        self._crntUbedTime = 0

        #500以上上昇したか
        self._suddenPriceUp = False
        self._suddenPriceTime = 0


        #ロスカット系
        self._isLossCut = False

        self._loadStatus()


    def update(self, tickDataList, stockstatClass):
        self._tickDataList = tickDataList
        self._stockstatClass = stockstatClass

        # sclalerを使うためにめんどくさい処理をする。。
        priceList = [self._tickDataList[i][1] for i in range(len(self._tickDataList))]
        npPriceList = np.array(priceList).reshape(len(priceList), 1)
        self._scaler.fit_transform(npPriceList)

        #ボリンジャー下抜け調査
        self.checkCrossingLowBolling()

        #ゴールデンクロスチェック
        # self.checkGoldenXed_MacdH()
        self.checkGoldenXed_MacdS()
        # self.checkGoldenXed_MacdS2()

        #バンド上抜け調査
        self.checkCrossingHighBolling()

        # 500以上上昇したか
        self.checkSuddenPriceUp()

        # if(len(self._params) > 0):
        #     for param_ in self._params:
        #         self._stockstatClass.get(param_)



    def buySignal(self, dryRun=True):
        macdhAll = self._stockstatClass.get('macdh') # grey
        rsiAll = self._stockstatClass.get('rsi_9')
        crntTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        # if len(macdhAll) > 4 :
        #     print("buySignal {}, 1>2:{}, 2>3:{}".format(crntTime, (macdhAll[TICK_NEWEST] > macdhAll[-2]), (macdhAll[-2] > macdhAll[-3])))
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]

        # if(self._tickDataList[TICK_NEWEST][0] == 20180228103158):
        #     print("test")

        crntPrice = float(self._tickDataList[TICK_NEWEST][1])
        if(
            # 共通項目
            (
                len(macdhAll) > 3 and
                self._buyNum == 0
            ) and
            (
                #GX狙いロジック
                (
                    # 3連続右肩上がり
                    macdhAll[TICK_NEWEST] > macdhAll[-2] and macdhAll[-2] > macdhAll[-3] and
                    # ボリンジャーを用いた買いロジック
                    self._buyLogic_Boll_GX()
                )
                #　一旦OFF 2018/03/15
                # or
                # #バンドウォーク狙いロジック
                # (
                #     #バンドの上を推移
                #     self._buyLogic_Boll_UB()
                # )
            )
        ):

            self._buyNum += 1
            # 最安で買うか現時点での値段で買うか。。
            # if(float(crntPrice) > float(self._bollLBXPrice)):
            #     self._buyPrice = float(self._bollLBXPrice)
            # else:
            self._buyPrice = crntPrice
            self._buyDateTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]

            # 最低売り金額を算出
            self._sellPrice = self.getMinSellPrice(self._buyPrice, self._coinAmount, self._minEarn)[0]
            print("***Buy! {} price:{}, macd:{}, rsi:{}, self._sellPrice:{}, goldedXedTime:{}".format(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME], self._buyPrice, macdhAll[TICK_NEWEST], rsiAll[TICK_NEWEST], self._sellPrice, self._goldedXedTime))

            # self._saveStatus()

            return self._buyPrice

        return 0



    def _buyLogic_Boll_GX(self):
        bollLbAll = self._stockstatClass.get('boll_lb')
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]
        crntTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        print("_buyLogic_Boll_GX {}: hasLB:{}, aboveLB:{}, isX:{}, rsi:{}, scaledprice:{}".format(crntTime, self._hasLowerBollLb, self.isAboveLowBoll(), self.stillGoldenXed(), self._stockstatClass.get('rsi_9')[TICK_NEWEST], scaledPrice))
        if(
            #ボリンジャーLBが存在する
            math.isnan(bollLbAll[TICK_NEWEST]) == False and
            bollLbAll[TICK_NEWEST] > 0.0 and
            #ボリンジャーLBを下回った事がある。
            self._hasLowerBollLb and
            #今は上回っている
            self.isAboveLowBoll() and

            #ゴールデンクロス発生中
            self.stillGoldenXed() and



            # rsiに値が入っていること
            math.isnan(self._stockstatClass.get('rsi_9')[TICK_NEWEST]) == False and
            self._stockstatClass.get('rsi_9')[TICK_NEWEST] < 60.0 and

            # 高値の時は買わない（0.25? 0.44?）
            scaledPrice < 0.25 and
            # 0に行くとさらに下がる可能性があるので
            scaledPrice > 0.05
        ):
            print("***Buy logic:[_buyLogic_Boll_GX] True")
            return True
        return False


    """
        バンドの上で推移する場合の買いロジック
        過去二つのロウソクは上昇
        
    """
    def _buyLogic_Boll_UB(self):
        highAll = self._stockstatClass.get('high')
        closeAll = self._stockstatClass.get('close')
        rsiAll = self._stockstatClass.get('rsi_9')
        macdAll = self._stockstatClass.get('macd') # orange
        macdsAll = self._stockstatClass.get('macds') # yellow
        crntPrice = self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE]

        crntCandleType = self.getCandleType(TICK_NEWEST)
        prevCandleType = self.getCandleType(-2)

        bandratio = self._getBandBolaRatio()

        # print("***buyLogic_Boll_UB: hasBollUbed:{}, isBoll_UBed:{}".format(self._hasBollUbed, self.isBoll_UBed()))


        if(
            len(closeAll) > 2 and
            # #バンドの上抜け期間中
            #上抜けした回数が規定より上回っている
            self.isBoll_UBed() and
            # 500以上上昇したことがある
            self._suddenPriceUp and
            # 今のろうそくは大丈夫か
            self.getCandleType() == CANDLETYPE_POS
        ):
            print("***Buy logic:[_buyLogic_Boll_UB] crntPrice:{}, closeAll2:{}, highAll2:{}, bandratio:{}".format(crntPrice, closeAll[-2], highAll[-2], bandratio))
            return True
        return False



    def sellSignal(self, dryRun=True):
        macdAll = self._stockstatClass.get('macd')
        rsiAll = self._stockstatClass.get('rsi_9')

        crntPrice = float(self._tickDataList[TICK_NEWEST][1])
        scaledPrice = self._scaler.transform(crntPrice)[0][0]
        if(
            self._buyNum > 0.0 and
            #値上がりしてること
            float(crntPrice) >= float(self._sellPrice)
        ):
            self._buyNum -= 1
            self._sellPrice = crntPrice
            #利益算出
            earnedVal = self._sellPrice - self._buyPrice
            self._totalEarned += earnedVal
            print("***Sell! {} price:{}, macd:{}, rsi:{}, totalEarned:{}".format(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME], crntPrice, macdAll[TICK_NEWEST], rsiAll[TICK_NEWEST], self._totalEarned))

            # 売ったら指標パラメータリセット
            self.resetBuySellParams()
            return self._sellPrice

        return 0



    """
    買った金額、個数から「利益額」を出す為に0.001コインあたりいくらでうればいいかを算出
    :param minEarn 売らなければならないコインを全て売った時の利益額

    return: [1コイン辺りの最低売り金額, 買いの時との差, 売らなければいけないコイン個数] 
    """
    def getMinSellPrice(self, buyPrice, coinAmount=0.001, minEarn=1.0):
        minAmount = 0.001
        buyPrice = float(buyPrice)
        coinAmount = float(coinAmount)
        minEarn = float(minEarn)

        # 10万円以下手数料
        extraFee = self._extraFeeList[0]
        # 実際に払った金額
        actualBuyPrice = buyPrice * coinAmount

        # 50万以下だったら0.14%
        if (actualBuyPrice > 100000.0 and actualBuyPrice <= 500000.0):
            extraFee = self._extraFeeList[0]

        # 0.01あたりに直す
        ratio = minAmount / coinAmount

        # 0.001あたりの手数料（x2。買い＆売り）
        minExtraFee = actualBuyPrice * extraFee * ratio * 2

        # 0.001あたりの金額
        minActualBuyPrice = buyPrice * minAmount

        # 0.001あたりの最低売り価格 (minEarn*ratioをする事で「全部売ればminEarnになる」)
        possibleSellPrice = minActualBuyPrice + minExtraFee + (minEarn*ratio)

        # 1コインに置き換える
        coinSellPrice = possibleSellPrice / minAmount

        # 1コインあたりのdiff
        diffPrice = coinSellPrice - buyPrice

        return [coinSellPrice, diffPrice, coinAmount]



    """
        バンドLBを下抜けたかどうかの判断
        ロウソクの下ヒゲが当たったら_hasLowerBollLbをON
    """
    def checkCrossingLowBolling(self):
        tmpTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        crntTime = int(str(tmpTime)[:12])
        if(
            len(self._stockstatClass) > 3 and
            #ちゃんと値が入っていること
            math.isnan(self._stockstatClass.get('boll_lb')[TICK_NEWEST]) == False and
            self._stockstatClass.get('boll_lb')[TICK_NEWEST] > 0.0 and
            #ボリンジャーLB価格で比較
            self._stockstatClass.get('low')[TICK_NEWEST] < self._stockstatClass.get('boll_lb')[TICK_NEWEST] and
            #lowがちゃんとした値であること
            self._stockstatClass.get('low')[TICK_NEWEST] > 0.0 and
            #下抜け期間である
            (
                self._lowerBollLbTime == 0 or
                crntTime - self._lowerBollLbTime <= LBED_INTERVAL
            )
        ):
            print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self._tickDataList[TICK_NEWEST][0], self._stockstatClass.get('low')[TICK_NEWEST], self._stockstatClass.get('boll_lb')[TICK_NEWEST]))
            self._bollLBXPrice = self._stockstatClass.get('low')[TICK_NEWEST]
            self._possibleSellPrice = self._bollLBXPrice + 3
            self._hasLowerBollLb = True
            self._lowerBollLbTime = crntTime
            return True


        if(self._hasLowerBollLb and crntTime - self._lowerBollLbTime > LBED_INTERVAL):
            print("Crossed LB RESET!: time:{}, low:{}, boll_lb:{},".format(self._tickDataList[TICK_NEWEST][0], self._stockstatClass.get('low')[TICK_NEWEST], self._stockstatClass.get('boll_lb')[TICK_NEWEST]))
            self._hasLowerBollLb = False
            self._lowerBollLbTime = 0

        return False




    """
        ボリンジャーバンドLBの上になったかの判断
    """
    def isAboveLowBoll(self):
        if(self._stockstatClass.get('low')[TICK_NEWEST] > self._stockstatClass.get('boll_lb')[TICK_NEWEST]):
            return True
        return False




    def isCrossingMidBolling(self):
        if(self._stockstatClass.get('low')[TICK_NEWEST] > self._stockstatClass.get('boll')[TICK_NEWEST]):
            return True
        return False



    def checkCrossingHighBolling(self, time=TICK_NEWEST):
        highAll = self._stockstatClass.get('high')
        if(len(highAll) < 3):
            return False
        bollUbAll = self._stockstatClass.get('boll_ub')

        tmpTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        crntTime = int(str(tmpTime)[:12])
        crntPrice = self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE]

        if(self._hasBollUbed == False):
            #上抜いた時カウント始め
            if(float(crntPrice) - float(bollUbAll[TICK_NEWEST]) > 0):
                self._hasBollUbed = True
                self._bollUbedTime = crntTime
                self._bollUbedInterval = 1
                print("checkCrossingHighBolling => Begin: {}, _bollUbedInterval:{}, bollUbedNum:{}".format(crntTime, self._bollUbedInterval, self._bollUbedNum))

        else:
            if(crntTime - self._bollUbedTime == 1):
                self._bollUbedTime = crntTime
                self._bollUbedInterval += 1
                print("checkCrossingHighBolling => Update: {}, _bollUbedInterval:{}, bollUbedNum:{}".format(crntTime, self._bollUbedInterval, self._bollUbedNum))

            elif(self._bollUbedInterval >= GOLDENXED_INTERVAL):
                self._hasBollUbed = False
                self._bollUbedInterval = 0
                #上抜け回数の方もリセット
                self._bollUbedNum = 0
                self._crntUbedTime = 0
                print("checkCrossingHighBolling => False: {}, _bollUbedInterval:{}, bollUbedNum:{}".format(crntTime, self._bollUbedInterval, self._bollUbedNum))

        return False


    """
        バンド上限にタッチした期間かどうか
        期間内に500以上値上がりしたかどうか
        4足目まで継続
    """
    def isBoll_UBed(self):
        if(len(self._tickDataList) <= 0):
            return False

        bollUbAll = self._stockstatClass.get('boll_ub')

        tmpTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        crntTime = int(str(tmpTime)[:12])
        crntPrice = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE])
        # 上限突破した期間内にタッチしたかどうか
        if(self._hasBollUbed):
            if(crntPrice > float(bollUbAll[TICK_NEWEST]) and self._crntUbedTime != crntTime):
                self._bollUbedNum += 1
                self._crntUbedTime = crntTime
                # print("******isBoll_UBed1:{}, bollUbedNum:{}".format(crntTime, self._bollUbedNum))

            # 3回以上タッチしたらUbした。
            if(self._bollUbedNum >= 3):
                # print("******isBoll_UBed2:{}".format(crntTime))
                return True

        return False


    """
        ゴールデンクロスチェック（MacdHとMacd使用）
        時間、フラグ更新
    """
    def checkGoldenXed_MacdH(self):
        allMacdH = self._stockstatClass.get('macdh') # grey
        allMacd = self._stockstatClass.get('macd') # orange
        if(len(allMacdH) <= 2):
            return

        if (
            len(allMacdH) > 1 and len(allMacd) > 1 and
            # macdHの一番最新は確実に上回っている事
            allMacdH[TICK_NEWEST] - allMacd[TICK_NEWEST] > 0 and
            # 2番目はMacdHが低い
            allMacdH[-2] - allMacd[-2] < 0
        ):
            self._isGoldedXed = True
            crntTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
            self._goldedXedTime = int(str(crntTime)[:12])


    """
        ゴールデンクロスチェック（MacdHとMacdS使用）
        時間、フラグ更新
        最初反応がmacdhを使用していたが、反応が早すぎる事がある。macdとmacdsに変更。
        TICK_NEWESTはアップダウンが激しいため-2,-3で比較
    """
    def checkGoldenXed_MacdS(self):
        allMacdH = self._stockstatClass.get('macdh') # grey
        allMacdS = self._stockstatClass.get('macds') # yellow
        allRsi = self._stockstatClass.get('rsi_9')
        if(len(allMacdH) <= 2):
            return

        crntTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        # print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(crntTime, (allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdS[-2] - allMacdH[-2])))

        if (
            len(allMacdH) > 2 and len(allMacdS) > 2 and
            # macdの一番最新は確実に上回っている事
            allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST] > 0 and
            # 2番目はMacdSが低い
            allMacdH[-2] - allMacdS[-2] < 0
        ):
            print("checkGoldenXed_MacdS {} macd1:{}, macd2:{}".format(crntTime, (allMacdH[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdH[-2] - allMacdS[-2])))
            self._isGoldedXed = True
            self._goldedXedTime = int(str(crntTime)[:12])



    """
        ゴールデンクロスチェック（MacdとMacdS使用）
        時間、フラグ更新
        反応は一番遅い。
    """
    def checkGoldenXed_MacdS2(self):
        allMacd = self._stockstatClass.get('macd') # orange
        allMacdS = self._stockstatClass.get('macds') # yellow
        allRsi = self._stockstatClass.get('rsi_9')
        if(len(allMacd) <= 2):
            return

        crntTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        # print("checkGoldenXed_MacdS2 {} macd1:{}, macd2:{}".format(crntTime, (allMacd[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacdS[-2] - allMacd[-2])))

        if (
            len(allMacd) > 2 and len(allMacdS) > 2 and
            # macdの一番最新は確実に上回っている事
            allMacd[TICK_NEWEST] - allMacdS[TICK_NEWEST] > 0 and
            # 2番目はMacdSが低い
            allMacd[-2] - allMacdS[-2] < 0
        ):
            print("checkGoldenXed_MacdS2 {} macd1:{}, macd2:{}".format(crntTime, (allMacd[TICK_NEWEST] - allMacdS[TICK_NEWEST]), (allMacd[-2] - allMacdS[-2])))
            self._isGoldedXed = True
            self._goldedXedTime = int(str(crntTime)[:12])



    """
        ゴールデンクロス期間かどうか
        4足目まで継続
    """
    def stillGoldenXed(self):
        if(len(self._tickDataList) <= 0):
            return False

        tmpTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        crntTime = int(str(tmpTime)[:12])
        # クロスした
        if(self._isGoldedXed):
            # クロス期間内
            if((crntTime - self._goldedXedTime) <= GOLDENXED_INTERVAL):
                return True
            # クロス期間外
            else:
                self._isGoldedXed = False

        return False



    """
        ゴールデンクロス時にはもう遅い。
        差が大きく開いたところを狙う。
    """
    def willGoldenX(self):
        macdAll = self._stockstatClass.get('macd')
        macdsall = self._stockstatClass.get('macds')
        macdDif1 = macdsall[TICK_NEWEST] - macdAll[TICK_NEWEST]
        macdDif2 = macdsall[-2] - macdAll[-2]
        macdDif3 = macdsall[-3] - macdAll[-3]

        # print("macdDiff:{}, {}, {}".format(macdDif1, macdDif2, macdDif3))
        if(macdDif1 > macdDif2 and macdDif2 > macdDif3):
            return True

        return False



    """
        過去（-2）のopen, closeが500以上上昇したかどうかチェック
    """
    def checkSuddenPriceUp(self):
        closeAll = self._stockstatClass.get('close')
        openAll = self._stockstatClass.get('open')

        if(len(closeAll) < 2):
            return

        crntTime = int(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME])

        # 期間スタート
        if(self._suddenPriceUp == False and closeAll[TICK_NEWEST] - openAll[TICK_NEWEST] > SUDDEN_PRICE_UP):
            # print("checkSuddenPriceUp: {}, diff:{}".format(crntTime, (closeAll[-2] - openAll[-2])))
            self._suddenPriceUp = True
            self._suddenPriceTime = crntTime

        # 期間外になったらリセット
        elif(crntTime - self._suddenPriceTime > SUDDEN_PRICE_UP_INTERVAL):
            self._suddenPriceUp = False
            self._suddenPriceTime = 0



    """
        各指標のパラメータのリセット
        sellしたと同時にする
    """
    def resetBuySellParams(self):
        self._isGoldedXed = False
        self._hasLowerBollLb = False
        self._buyPrice = 0
        self._buyDateTime = None
        self._sellPrice = 0
        self._buyNum = 0
        self._bollLBXPrice = 0
        self._possibleSellPrice = 0
        self._goldedXedTime = 0
        self._isLossCut = False

        self._hasBollUbed = False
        self._bollUbedTime = 0
        self._bollUbedInterval = 0
        self._bollUbedNum = 0

        self._buyOrderId = ""
        self._sellOrderId = ""

        self._deleteStatus()



    def _getBandBolaRatio(self):
        allBollUb = self._stockstatClass.get('boll_ub')
        allBollLb = self._stockstatClass.get('boll_lb')

        if(len(allBollUb) < 3 or (math.isnan(allBollUb[TICK_NEWEST] == False or math.isnan(allBollLb[TICK_NEWEST]) == False))):
            return []

        crntBollRatio = (allBollUb[TICK_NEWEST] - allBollLb[TICK_NEWEST])/allBollUb[TICK_NEWEST]
        prevBollRatio2 = (allBollUb[-2] - allBollLb[-2])/allBollUb[-2]
        prevBollRatio3 = (allBollUb[-3] - allBollLb[-3])/allBollUb[-3]

        return [crntBollRatio, prevBollRatio2, prevBollRatio3]


    """
        買って売りを出した後、3足たってもバンド幅が1%の上昇を始めない場合、
        最低限の売値の値段を返す
    """
    def decideLossCut(self):
        if(self._sellPrice <= 0):
            return [None, 0]

        # 分に直して比較。3分間のロウソクで確認
        crntDateTime = self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME]
        crntDateTime = int(str(crntDateTime)[:12])
        boughtDateTime = int(str(self._buyDateTime)[:12])
        if(crntDateTime - boughtDateTime < 3):
            return [None, 0]


        macdhAll = self._stockstatClass.get('macdh') # grey
        macdAll = self._stockstatClass.get('macd') # orange
        macdsAll = self._stockstatClass.get('macds') # yellow
        crntPrice = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE])
        # [第二段階]
        # 第一段階後
        # デッドクロス
        # LBをクロスしている
        if(
            len(macdAll) > 2 and
            self._isLossCut == True and
            (macdAll[-2] - macdsAll[-2] > 0 and macdAll[TICK_NEWEST] - macdsAll[TICK_NEWEST] < 0) and
            self.checkCrossingLowBolling()
        ):
            oldSellPrice = self._sellPrice
            self._sellPrice = crntPrice
            print("***LosCut Lv2! {}, buyPrice:{}, oldSellPrice:{}, newSellPrice:{}".format(crntDateTime, self._buyPrice, oldSellPrice, self._sellPrice))
            # self._saveStatus()
            return [self._buyOrderId, self._sellPrice]


        # 第最終段階
        # 第一段階後
        # 2万以上差がついた
        # 2時間以上時間がたっても戻らない
        if (
            self._isLossCut == True and
            crntPrice - self._buyPrice <= -20000.0 and
            crntDateTime - boughtDateTime >= LOSSCUT_FINAL_TIMEINTERVAL
        ):
            oldSellPrice = self._sellPrice
            self._sellPrice = crntPrice
            print("***LosCut Lv3! {}, buyPrice:{}, oldSellPrice:{}, newSellPrice:{}".format(crntDateTime, self._buyPrice, oldSellPrice, self._sellPrice))
            # self._saveStatus()
            return [self._buyOrderId, self._sellPrice]


        # 第一段階
        if(self._isLossCut):
            return [None, 0]


        oldSellPrice = self._sellPrice
        bandlist = self._getBandBolaRatio()
        if(
            len(bandlist) > 2 and
            # 順当に上がっていない
            (bandlist[TICK_NEWEST] > bandlist[-2] and bandlist[-2] > bandlist[-3]) == False and
            #3足で1%以上の上昇をしていない
            bandlist[TICK_NEWEST] - bandlist[-3] < 0.001
        ):
            # 最低限の売り値取得（0.5円以上の利益をだす）
            lowestPrice = self.getMinSellPrice(self._buyPrice, self._coinAmount, 0.5)[0]
            # 現在の値段の方が高かったらそっちを使用
            if(crntPrice > lowestPrice):
                self._sellPrice = crntPrice
            else:
                self._sellPrice = lowestPrice

        self._isLossCut = True
        print("***LosCut Lv1! {}, buyPrice:{}, oldSellPrice:{}, newSellPrice:{}".format(crntDateTime, self._buyPrice, oldSellPrice, self._sellPrice))

        # self._saveStatus()

        return [self._buyOrderId, self._sellPrice]



    def getCandleType(self, timePrev=TICK_NEWEST):
        highAll = self._stockstatClass.get('high')

        if(len(highAll) < 3):
            return CANDLETYPE_NEG

        lowAll = self._stockstatClass.get('low')
        crntPrice = float(self._tickDataList[TICK_NEWEST][TICK_PARAM_PRICE])
        prevPrice = float(self._tickDataList[-2][TICK_PARAM_PRICE])

        # 現在のロウソクはまだできてないのでTickデータを使用
        if(timePrev == TICK_NEWEST):
            if(crntPrice - prevPrice > 0):
                return CANDLETYPE_POS
            return CANDLETYPE_NEG

        # ロウソクができていればそれを使用
        if(highAll[timePrev] > lowAll[timePrev]):
            return CANDLETYPE_POS
        return CANDLETYPE_NEG


    def _saveStatus(self):
        saveParam = {
            'buyPrice': self._buyPrice,
            'buyDateTime' : self._buyDateTime,
            'sellPrice' : self._sellPrice,
            'coinAmount' : self._coinAmount,
            'minEarn': self._minEarn,
            'buyNum': self._buyNum,
            'isLossCut': self._isLossCut,
            'buyOrderId': str(self._buyOrderId),
            'sellOrderId': str(self._sellOrderId),
        }

        with open(STATUS_FILEPATH, 'w', encoding='utf-8') as outfile:
            json.dump(saveParam, outfile)


    def _loadStatus(self):
        if(os.path.exists(STATUS_FILEPATH)):
            params = json.load(open(STATUS_FILEPATH))
            self._buyPrice = float(params['buyPrice'])
            self._buyDateTime = float(params['buyDateTime'])
            self._sellPrice = float(params['sellPrice'])
            self._coinAmount = float(params['coinAmount'])
            self._minEarn = float(params['minEarn'])
            self._buyNum = float(params['buyNum'])
            self._isLossCut = float(params['isLossCut'])
            self._buyOrderId = str(params['buyOrderId'])
            self._sellOrderId = str(params['sellOrderId'])


    def _deleteStatus(self):
        if (os.path.exists(STATUS_FILEPATH)):
            os.remove(STATUS_FILEPATH)



    def updateStatus(self, side, orderId):
        if(side=="buy"):
            self._buyOrderId = str(orderId)
            self._sellOrderId = ""
        elif (side == "sell"):
            self._sellOrderId = str(orderId)
            self._buyOrderId = ""

        if(orderId):
            self._saveStatus()
