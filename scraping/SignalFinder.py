import pandas as pd
import time
import numpy as np
import scraping
import math


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

class SignalFinder():
    def __init__(self, kabucom):
        self._kabucom = kabucom
        self._alldata = []
        self._stockstatClass = None

        #買った際にincrement
        self._buyNum = 0
        self._buyPrice = 0

        self._sellPrice = 0

        self._scaler = MinMaxScaler(feature_range=(0, 1))

        #ボリンジャーバンドを下抜けた際の値段
        self._bollLBXPrice = 0
        #最低額はboll_lb+3
        self._possibleSellPrice = 0
        #ボリンジャーバンドを下抜けた事がある
        self._hasLowerBollLb = False

        self.update()


    def update(self):
        self._stockstatClass = self._kabucom.convertToStockStats(['macd', 'macds', 'macdh', 'rsi_9', 'boll', 'boll_ub', 'boll_lb'])
        self._alldata = self._stockstatClass.as_matrix(columns=['open', 'high', 'low', 'close', 'volume', 'macd', 'macds', 'macdh', 'rsi_9', 'boll', 'boll_ub', 'boll_lb'])
        if len(self._alldata) > 0:
            # datetime price volume
            self._stockTicks = self._kabucom._stockTicks

            #ボリンジャーLBに触れたかどうか
            self.isCrossingLowBolling()

            #sclalerを使うためにめんどくさい処理をする。。
            priceList = [self._stockTicks[i][1] for i in range(len(self._stockTicks))]
            npPriceList = np.array(priceList).reshape(len(priceList), 1)
            self._scaler.fit_transform(npPriceList)

            date = self._stockTicks[TICK_NEWEST][0]
            price = self._stockTicks[TICK_NEWEST][1]
            macd1 = self._alldata[:, PARAM_MACD][TICK_NEWEST]
            macd2 = 0
            macd3 = 0
            macds = 0
            macdh = 0
            rsi = 0
            boll = 0
            boll_lb = 0
            if(len(self._alldata)>3):
                macd2 = self._alldata[:, PARAM_MACD][-2]
                macd3 = self._alldata[:, PARAM_MACD][-3]
                macds = self._alldata[:, PARAM_MACDS][TICK_NEWEST]
                macdh = self._alldata[:, PARAM_MACDH][TICK_NEWEST]
                rsi = self._alldata[:, PARAM_RSI][TICK_NEWEST]
                boll = self._alldata[:, PARAM_BOLL][TICK_NEWEST]
                boll_lb = self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST]

            pos = self._scaler.transform(price)
            print("date:{}, price:{}, pos:{}, macd:{}, macds:{}, boll:{}, boll_lb:{}, rsi: {}".format(date, price, pos, macd1, macds, boll, boll_lb, rsi))
            # print("date:{}, price:{}, macd-1:{}, macd-2:{}, macd-3:{}, rsi:{}, boll_ub:{}".format(date, price, macd1, macd2, macd3, rsi, boll_ub))
            # print("date:{}, price:{}, macd-1:{}, rsi:{}, boll_ub:{}".format(date, price, macd1, rsi, boll_ub))





    def buySignal(self):
        macdAll = self._alldata[:, PARAM_MACD]
        rsiAll = self._alldata[:, PARAM_RSI]
        # print(macdAll)
        # print()
        scaledPrice = self._scaler.transform(self._stockTicks[TICK_NEWEST][1])[0][0]

        crntPrice = self._stockTicks[TICK_NEWEST][1]
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
            print("***Buy! {} price:{}, macd:{}, rsi:{}, self._sellPrice:{}".format(self._stockTicks[TICK_NEWEST][0], self._buyPrice, macdAll[TICK_NEWEST], rsiAll[TICK_NEWEST], self._sellPrice))
            return True

        return False



    def _buyLogic_MACD(self):
        macdAll = self._alldata[:, PARAM_MACD]
        rsiAll = self._alldata[:, PARAM_RSI]
        scaledPrice = self._scaler.transform(self._stockTicks[TICK_NEWEST][1])[0][0]

        if(
            # プラ転してきている
            macdAll[TICK_NEWEST] > 0 and macdAll[TICK_NEWEST] < 0.2 and
            # macdが上昇してきている(過去3番目、2番目と上がり調子）
            macdAll[-2] < macdAll[TICK_NEWEST] and
            macdAll[-3] < macdAll[-2] and
            # rsiが100の時は避ける
            rsiAll[TICK_NEWEST] < 100.0 and
            # 高値の時は買わない
            scaledPrice < 0.8
        ):
            return True

        return False


    def _buyLogic_Boll(self):
        macdAll = self._alldata[:, PARAM_MACD]
        bollAll = self._alldata[:, PARAM_BOLL]
        bollUbAll = self._alldata[:, PARAM_BOLL_UB]
        bollLbAll = self._alldata[:, PARAM_BOLL_LB]
        scaledPrice = self._scaler.transform(self._stockTicks[TICK_NEWEST][1])[0][0]
        print("_buyLogic_Boll: {}, {}, {}".format(self._hasLowerBollLb, self.isAboveLowBoll(), self.willGoldenX()))
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
            math.isnan(self._alldata[:, PARAM_RSI][TICK_NEWEST]) == False and
            self._alldata[:, PARAM_RSI][TICK_NEWEST] < 60.0 and
            # 高値の時は買わない
            scaledPrice < 0.2 and
            # 0に行くとさらに下がる可能性があるので
            scaledPrice > 0.05
        ):
            return True



    def sellSignal(self):
        macdAll = self._alldata[:, 5]
        rsiAll = self._alldata[:, 6]

        crntPrice = self._stockTicks[TICK_NEWEST][1]
        scaledPrice = self._scaler.transform(crntPrice)[0][0]
        if(
            self._buyNum > 0.0 and
            #3円以上値上がりしてること（手数料があるため）
            float(crntPrice) > float(self._buyPrice) and#+ self._kabucom.neededPrice(crntPrice) and

            #macdが上がってる時
            # self._sellLogic_MACD()

            #ボリンジャー判断
            self._sellLogic_Boll()
        ):
            self._buyNum -= 1
            self._sellPrice = crntPrice
            print("***Sell! {} price:{}, macd:{}, rsi:{}".format(self._stockTicks[TICK_NEWEST][0], crntPrice, macdAll[TICK_NEWEST], rsiAll[TICK_NEWEST]))
            return True

        return False


    def _sellLogic_MACD(self):
        macdAll = self._alldata[:, 5]
        rsiAll = self._alldata[:, 6]

        crntPrice = self._stockTicks[TICK_NEWEST][1]
        scaledPrice = self._scaler.transform(crntPrice)[0][0]

        if(
            # macdが上がってる時
            macdAll[TICK_NEWEST] > 0.7
        ):
            return True

        return False


    def _sellLogic_Boll(self):
        macdAll = self._alldata[:, PARAM_MACD]
        macdsAll = self._alldata[:, PARAM_MACDS]
        macdhAll = self._alldata[:, PARAM_MACDH]

        bollAll = self._alldata[:, PARAM_BOLL]
        bollUbAll = self._alldata[:, PARAM_BOLL_UB]
        bollLbAll = self._alldata[:, PARAM_BOLL_LB]
        scaledPrice = self._scaler.transform(self._stockTicks[TICK_NEWEST][1])[0][0]

        if(
            # midより上になった
            self.isCrossingMidBolling() and
            #macdがsignalを上回った
            macdAll[TICK_NEWEST] > macdsAll[TICK_NEWEST] and
            #ゴールデンクロス
            self.isGoldenXed() and
            # 過去にあった中で比較的高額
            scaledPrice > 0.7
        ):
            return True

        return False



    """
        ボリンジャーバンドLBを下抜けたかどうかの判断
        ロウソクの下ヒゲが当たったら_hasLowerBollLbをON
    """
    def isCrossingLowBolling(self):
        if(
            len(self._alldata) > 3 and
            #ちゃんと値が入っていること
            math.isnan(self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST]) == False and
            self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST] > 0.0 and
            #ボリンジャーLB価格で比較
            self._alldata[:, PARAM_LOW][TICK_NEWEST] < self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST] and
            #_hasLowerBollLbのフラグが立つのでRSIがセットされてない場合はスキップ
            self._alldata[:, PARAM_LOW][TICK_NEWEST] > 0.0

        ):
            print("Crossed LB!: time:{}, low:{}, boll_lb:{},".format(self._stockTicks[TICK_NEWEST][0], self._alldata[:, PARAM_LOW][TICK_NEWEST], self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST]))
            self._bollLBXPrice = self._alldata[:, PARAM_LOW][TICK_NEWEST]
            self._possibleSellPrice = self._bollLBXPrice + 3
            self._hasLowerBollLb = True
            return True
        return False



    """
        ボリンジャーバンドLBの上になったかの判断
    """
    def isAboveLowBoll(self):
        if(self._alldata[:, PARAM_LOW][TICK_NEWEST] > self._alldata[:, PARAM_BOLL_LB][TICK_NEWEST]):
            return True
        return False




    def isCrossingMidBolling(self):
        if(self._alldata[:, PARAM_LOW][TICK_NEWEST] > self._alldata[:, PARAM_BOLL][TICK_NEWEST]):
            return True
        return False


    def isCrossingHighBolling(self):
        if(self._alldata[:, PARAM_HIGH][TICK_NEWEST] > self._alldata[:, PARAM_BOLL_UB][TICK_NEWEST]):
            return True
        return False



    def isGoldenXed(self):
        if(self._alldata[:, PARAM_MACD][TICK_NEWEST] > self._alldata[:, PARAM_MACDS][TICK_NEWEST]):
            return True
        return False


    """
        ゴールデンクロス時にはもう遅い。
        差が大きく開いたところを狙う。
    """
    def willGoldenX(self):
        macdAll = self._alldata[:, PARAM_MACD]
        macdsall = self._alldata[:, PARAM_MACDS]
        macdDif1 = macdsall[TICK_NEWEST] - macdAll[TICK_NEWEST]
        macdDif2 = macdsall[-2] - macdAll[-2]
        macdDif3 = macdsall[-3] - macdAll[-3]

        # print("macdDiff:{}, {}, {}".format(macdDif1, macdDif2, macdDif3))
        if(macdDif1 > macdDif2 and macdDif2 > macdDif3):
            return True

        return False



if __name__ == '__main__':
    kabucom = scraping.kabucom.KabuComMainController()
    signalFinder = SignalFinder(kabucom)

    path = "./csv/stockTick_20180216_7201.csv"
    df = pd.read_csv(path)
    tmpList = df.values.tolist()
    for tick in tmpList:
        tmpTick = tick[1:]
        tmpTick[0] = int(tmpTick[0])
        #上記で実際のtickデータと同じにコンバート
        #下記でコントローラにストックしている状態にする
        kabucom._stockTicks.append(tmpTick)
        kabucom._statusUpdate()
        signalFinder.update()

        signalFinder.buySignal()
        signalFinder.sellSignal()

        # kabucom.makeGraph(kabucom.convertToStockStats())
        # time.sleep(0.1)


    kabucom.makeGraph(kabucom.convertToStockStats())
    kabucom.close()


