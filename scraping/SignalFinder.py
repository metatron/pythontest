import pandas as pd
import time
import numpy as np
import scraping

from sklearn.preprocessing import MinMaxScaler


class SignalFinder():
    def __init__(self, kabucom):
        self._kabucom = kabucom
        self.update()

        #買った際にincrement
        self._buyNum = 0
        self._buyPrice = 0

        self._sellPrice = 0

        self._scaler = MinMaxScaler(feature_range=(0, 1))


    def update(self):
        self._stockstatClass = self._kabucom.convertToStockStats(['macd', 'rsi_9'])
        self._alldata = self._stockstatClass.as_matrix(columns=['open', 'high', 'low', 'close', 'volume', 'macd', 'rsi_9'])
        if len(self._alldata) > 0:
            # datetime price volume
            self._stockTicks = self._kabucom._stockTicks

            #sclalerを使うためにめんどくさい処理をする。。
            priceList = [self._stockTicks[i][1] for i in range(len(self._stockTicks))]
            npPriceList = np.array(priceList).reshape(len(priceList), 1)
            self._scaler.fit_transform(npPriceList)

            date = self._stockTicks[-1][0]
            price = self._stockTicks[-1][1]
            macd1 = self._alldata[:, 5][-1]
            macd2 = 0
            macd3 = 0
            rsi = 0
            if(len(self._alldata)>3):
                macd2 = self._alldata[:, 5][-2]
                macd3 = self._alldata[:, 5][-3]
                rsi = self._alldata[:, 6][-1]
            print("date:{}, price:{}, macd-1:{}, macd-2:{}, macd-3:{}, rsi:{}".format(date, price, macd1, macd2, macd3, rsi))





    def buySignal(self):
        macdAll = self._alldata[:, 5]
        rsiAll = self._alldata[:, 6]
        # print(macdAll)
        # print()
        scaledPrice = self._scaler.transform(self._stockTicks[-1][1])[0][0]

        crntPrice = self._stockTicks[-1][1]
        if(
            len(macdAll) > 3 and
            self._buyNum == 0 and
            #プラ転してきている
            macdAll[-1] > 0 and  macdAll[-1] < 0.2 and
            #macdが上昇してきている(過去3番目、2番目と上がり調子）
            macdAll[-2] < macdAll[-1] and
            macdAll[-3] < macdAll[-2] and
            #rsiが100の時は避ける
            rsiAll[-1] < 100.0 and
            #高値の時は買わない
            scaledPrice < 0.8
        ):

            #売ったことがある場合値段チェック。
            #現在の株価がsellよりも低くないとだめ
            if(self._sellPrice > 0 and crntPrice + 3 >= self._sellPrice):
                return False

            self._buyNum += 1
            self._buyPrice = crntPrice
            print("***Buy! {} price:{}, macd:{}, rsi:{}, self._sellPrice:{}".format(self._stockTicks[-1][0], self._buyPrice, macdAll[-1], rsiAll[-1], self._sellPrice))
            return True

        return False


    def sellSignal(self):
        macdAll = self._alldata[:, 5]
        rsiAll = self._alldata[:, 6]

        crntPrice = self._stockTicks[-1][1]
        scaledPrice = self._scaler.transform(crntPrice)[0][0]
        if(
            self._buyNum > 0.0 and
            #3円以上値上がりしてること（手数料があるため）
            float(crntPrice) > float(self._buyPrice) + 3.0 and
            #macdが上がってる時
            macdAll[-1] > 0.7
        ):
            self._buyNum -= 1
            self._sellPrice = crntPrice
            print("***Sell! {} price:{}, macd:{}, rsi:{}".format(self._stockTicks[-1][0], crntPrice, macdAll[-1], rsiAll[-1]))
            return True

        return False




if __name__ == '__main__':
    kabucom = scraping.kabucom.KabuComMainController()
    signalFinder = SignalFinder(kabucom)

    path = "stockTick_20180215_7201.csv"
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

        # time.sleep(0.2)


    kabucom.makeGraph(kabucom.convertToStockStats())
    kabucom.close()


