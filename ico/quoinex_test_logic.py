from ico.quoinex_trade import QuoinexController
from ico.bit_buysell_logic import BitSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    quoinex = QuoinexController()
    # quoinex.initGraph()

    bitsignal = BitSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    tickFilePath = "./csv/tick_201803131014_BTC_JPY.csv"
    df = pd.read_csv(tickFilePath)
    tmpList = df.values.tolist()
    for tick in tmpList:
        tmpTick = tick[1:]
        tmpTick[0] = int(tmpTick[0])
        quoinex._tickList.append(tmpTick)
        quoinex._convertTickDataToCandle(quoinex._tickList)
        stockstatsClass = quoinex.convertToStockStats()

        bitsignal.update(quoinex._tickList, stockstatsClass)
        bitsignal.decideLossCut()
        bitsignal.buySignal()
        bitsignal.sellSignal()

        # print(quoinex._tickList[-1])
        # quoinex.makeGraph(quoinex.convertToStockStats())

        # index += 1
        # time.sleep(0.1)

    print("total Earned:{}".format(bitsignal._totalEarned))
    quoinex.initGraph()
    quoinex.makeGraph(quoinex.convertToStockStats(), False)


