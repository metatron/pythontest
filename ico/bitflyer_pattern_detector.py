from ico.bitflyer_trade import BitFlyerController
from ico.bit_buysell_logic import BitSignalFinder
from predictionclass.stock_pattern_detector import StockPatternDetect

import sklearn as sk
from sklearn.preprocessing import MinMaxScaler


import pandas as pd
import numpy as np
import time
from utils import addColumn



if __name__ == '__main__':
    bitflyer = BitFlyerController()
    # bitflyer.initGraph()

    bitsignal = BitSignalFinder(bitflyer._tickList, bitflyer._candleStats)

    tickFilePath = "./csv/tick_201803091545_BTC_JPY.csv"
    df = pd.read_csv(tickFilePath)
    tmpList = df.values.tolist()
    for tick in tmpList:
        tmpTick = tick[1:]
        tmpTick[0] = int(tmpTick[0])
        bitflyer._tickList.append(tmpTick)
        bitflyer._convertTickDataToCandle(bitflyer._tickList)
        stockstatsClass = bitflyer.convertToStockStats()

        bitsignal.update(bitflyer._tickList, stockstatsClass)
        bitsignal.decideLossCut()
        bitsignal.buySignal()
        bitsignal.sellSignal()

        # print(bitflyer._tickList[-1])
        # bitflyer.makeGraph(bitflyer.convertToStockStats())

        # index += 1
        # time.sleep(0.1)


    #AI Data preparation
    stock = bitflyer.convertToStockStats()
    allBasicData = np.array(stock.as_matrix(columns=['open', 'high', 'low', 'close']), dtype='float')
    basicScaler = MinMaxScaler(feature_range=(0, 1))
    allBasicDataNormalized = basicScaler.fit_transform(allBasicData)

    allMacdData = np.array(stock.as_matrix(columns=['macd', 'macdh', 'macds']), dtype='float')
    macdScaler = MinMaxScaler(feature_range=(0, 1))
    # allMacdDataNormalized = macdScaler.fit_transform(allMacdData)

    # allRsi = stock.get('rsi_9')
    # rsiScaler = MinMaxScaler(feature_range=(0, 1))
    # allRsiNormalized = rsiScaler.fit_transform(allRsi)
    #
    # allData = addColumn.add_column(allBasicData, allMacdDataNormalized[:len(allMacdDataNormalized)])

    trainX = None


    #AI training
    # spd = StockPatternDetect()



    print("total Earned:{}".format(bitsignal._totalEarned))
    bitflyer.initGraph()
    bitflyer.makeGraph(bitflyer.convertToStockStats(), False)


