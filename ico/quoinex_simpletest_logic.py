from ico.quoinex_trade import QuoinexController
from ico.simple_buysell_logic import SimpleSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    quoinex = QuoinexController()
    # quoinex.initGraph()

    simplesingal = SimpleSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    tickFilePath = "./csv/tick_201803061235_BTC_JPY.csv"
    df = pd.read_csv(tickFilePath)
    tmpList = df.values.tolist()
    for tick in tmpList:
        tmpTick = tick[1:]
        tmpTick[0] = int(tmpTick[0])
        quoinex._tickList.append(tmpTick)
        quoinex._convertTickDataToCandle(quoinex._tickList)
        stockstatsClass = quoinex.convertToStockStats()

        simplesingal.update(quoinex._tickList, stockstatsClass)
        # simplesingal.decideLossCut()
        simplesingal.buySignal()
        simplesingal.sellSignal()
        simplesingal._checkDeadXed_MacdS()

        # print(quoinex._tickList[-1])
        # quoinex.makeGraph(quoinex.convertToStockStats())

        # index += 1
        # time.sleep(0.1)

    print("total Earned:{}".format(simplesingal._totalEarned))
    quoinex.initGraph()
    quoinex.makeGraph(quoinex.convertToStockStats(), False)


