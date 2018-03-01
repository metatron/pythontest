import pandas as pd
import time
import numpy as np
import scraping
import math
import stockstats


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

# ゴールデンXから下記分間はXした時間
GOLDENXED_INTERVAL = 4

class BitSignalFinder():
    def __init__(self, tickDataList, stockstatClass, params=[]):

        if len(params) == 0:
            self._params = ['open', 'high', 'low', 'close', 'macd', 'macds', 'macdh', 'rsi_9', 'boll', 'boll_ub', 'boll_lb']
        else:
            self._params = params

        self._scaler = MinMaxScaler(feature_range=(0, 1))

        # 買った際にincrement
        self._buyNum = 0

        # 一番最後に買った時の値段
        self._buyPrice = 0

        # 一番最後に売った時の値段
        self._sellPrice = 0

        #コイン個数（ディフォルト0.001）
        self._coinAmount = 0.001

        #最低利益額（全coinAmount個ぶん売った時手数料をのぞいた最低利益額。円）
        self._minEarn = 2.0

        # トータル利益
        self._totalEarned = 0.0

        # ボリンジャーバンドを下抜けた際の値段
        self._bollLBXPrice = 0
        # 最低額はboll_lb+3
        self._possibleSellPrice = 0
        # ボリンジャーバンドを下抜けた事がある
        self._hasLowerBollLb = False
        # ゴールデンクロスになった事がある
        self._isGoldedXed = False
        self._goldedXedTime = 0


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
        self.checkGoldenXed()

        # if(len(self._params) > 0):
        #     for param_ in self._params:
        #         self._stockstatClass.get(param_)



    def buySignal(self):
        macdhAll = self._stockstatClass.get('macdh')
        rsiAll = self._stockstatClass.get('rsi_9')
        # if len(macdhAll) > 4 :
        #     print("buySignal 1>2:{}, 2>3:{}, _buyLogic_Boll:{}".format((macdhAll[TICK_NEWEST] > macdhAll[-2]), (macdhAll[-2] > macdhAll[-3]), self._buyLogic_Boll()))
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]

        crntPrice = self._tickDataList[TICK_NEWEST][1]
        if(
            len(macdhAll) > 3 and
            self._buyNum == 0 and

            # 3連続右肩上がり
            macdhAll[TICK_NEWEST] > macdhAll[-2] and macdhAll[-2] > macdhAll[-3] and

            #ボリンジャーを用いた売りロジック
            self._buyLogic_Boll()
        ):

            self._buyNum += 1
            # 最安で買うか現時点での値段で買うか。。
            # if(float(crntPrice) > float(self._bollLBXPrice)):
            #     self._buyPrice = float(self._bollLBXPrice)
            # else:
            self._buyPrice = crntPrice

            # 最低売り金額を算出
            self._sellPrice = self.getMinSellPrice(self._buyPrice, self._coinAmount, self._minEarn)[0]
            print("***Buy! {} price:{}, macd:{}, rsi:{}, self._sellPrice:{}".format(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME], self._buyPrice, macdhAll[TICK_NEWEST], rsiAll[TICK_NEWEST], self._sellPrice))
            return True

        return False



    def _buyLogic_Boll(self):
        bollLbAll = self._stockstatClass.get('boll_lb')
        scaledPrice = self._scaler.transform(self._tickDataList[TICK_NEWEST][1])[0][0]
        # print("_buyLogic_Boll: hasLB:{}, aboveLB:{}, isX:{}, rsi:{}, scaledprice:{}".format(self._hasLowerBollLb, self.isAboveLowBoll(), self.stillGoldenXed(), self._stockstatClass.get('rsi_9')[TICK_NEWEST], scaledPrice))
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

            # 高値の時は買わない
            scaledPrice < 0.25 and
            # 0に行くとさらに下がる可能性があるので
            scaledPrice > 0.05
        ):
            return True
        return False




    def sellSignal(self):
        macdAll = self._stockstatClass.get('macd')
        rsiAll = self._stockstatClass.get('rsi_9')

        crntPrice = self._tickDataList[TICK_NEWEST][1]
        scaledPrice = self._scaler.transform(crntPrice)[0][0]
        if(
            self._buyNum > 0.0 and
            #値上がりしてること
            float(crntPrice) >= float(self._sellPrice)
        ):
            self._buyNum -= 1
            self._sellPrice = crntPrice
            print("***Sell! {} price:{}, macd:{}, rsi:{}".format(self._tickDataList[TICK_NEWEST][TICK_PARAM_DATETIME], crntPrice, macdAll[TICK_NEWEST], rsiAll[TICK_NEWEST]))
            #利益算出
            earnedVal = self._sellPrice - self._buyPrice
            self._totalEarned += earnedVal

            # 売ったら指標パラメータリセット
            self.resetBuySellParams()
            return True

        return False



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
        extraFee = 0.0015
        # 実際に払った金額
        actualBuyPrice = buyPrice * coinAmount

        # 50万以下だったら0.14%
        if (actualBuyPrice > 100000.0 and actualBuyPrice <= 500000.0):
            extraFee = 0.0014

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
        ボリンジャーバンドLBを下抜けたかどうかの判断
        ロウソクの下ヒゲが当たったら_hasLowerBollLbをON
    """
    def checkCrossingLowBolling(self):
        if(
            len(self._stockstatClass) > 3 and
            #ちゃんと値が入っていること
            math.isnan(self._stockstatClass.get('boll_lb')[TICK_NEWEST]) == False and
            self._stockstatClass.get('boll_lb')[TICK_NEWEST] > 0.0 and
            #ボリンジャーLB価格で比較
            self._stockstatClass.get('low')[TICK_NEWEST] < self._stockstatClass.get('boll_lb')[TICK_NEWEST] and
            #lowがちゃんとした値であること
            self._stockstatClass.get('low')[TICK_NEWEST] > 0.0

        ):
            # print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self._tickDataList[TICK_NEWEST][0], self._stockstatClass.get('low')[TICK_NEWEST], self._stockstatClass.get('boll_lb')[TICK_NEWEST]))
            self._bollLBXPrice = self._stockstatClass.get('low')[TICK_NEWEST]
            self._possibleSellPrice = self._bollLBXPrice + 3
            self._hasLowerBollLb = True



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


    def isCrossingHighBolling(self):
        if(self._stockstatClass.get('high')[TICK_NEWEST] > self._stockstatClass.get('boll_ub')[TICK_NEWEST]):
            return True
        return False



    """
        ゴールデンクロスチェック
        時間、フラグ更新
    """
    def checkGoldenXed(self):
        allMacdH = self._stockstatClass.get('macdh')
        allMacd = self._stockstatClass.get('macd')
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
        各指標のパラメータのリセット
        sellしたと同時にする
    """
    def resetBuySellParams(self):
        self._isGoldedXed = False
        self._hasLowerBollLb = False
        self._buyPrice = 0
        self._sellPrice = 0
        self._buyNum = 0
        self._bollLBXPrice = 0
        self._possibleSellPrice = 0
        self._goldedXedTime = 0

