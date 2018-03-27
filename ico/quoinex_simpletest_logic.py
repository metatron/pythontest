from ico.quoinex_trade import QuoinexController
from ico.simple_buysell_logic import SimpleSignalFinder
import pandas as pd
import numpy as np
import time


MAX_RETRY_COUNT = 100

if __name__ == '__main__':
    quoinex = QuoinexController()
    # quoinex.initGraph()

    simplesingal = SimpleSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    index=0
    crntOrderId = ""
    side = ""
    retryCount = 0

    tickFilePath = "./csv/tick_quoinex_201803271624_BTC_JPY.csv"
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
        buyPrice = simplesingal.buySignal()
        sellPrice = simplesingal.sellSignal()
        simplesingal._checkDeadXed_MacdS()

        if(buyPrice > 0):
            side = "buy"
            crntOrderId = "buyXXXX" # quoinex.orderCoinRequest(side, buyPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)

        if(sellPrice > 0):
            side = "sell"
            crntOrderId = "sellXXXX" # quoinex.orderCoinRequest(side, sellPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)

        if(crntOrderId != ""):
            status = "filled"
            if(status == "filled"):
                if(side == "sell"):
                    simplesingal.resetParamsForBuy()
                crntOrderId = ""
                side = ""
                retryCount = 0
            elif(status == "live"):
                retryCount += 1

            if(retryCount >= MAX_RETRY_COUNT):
                quoinex.cancelOrder(crntOrderId)

        # print(quoinex._tickList[-1])
        # quoinex.makeGraph(quoinex.convertToStockStats())

        # index += 1
        # time.sleep(0.1)

    print("total Earned:{}".format(simplesingal._totalEarned))
    quoinex.initGraph()
    quoinex.makeGraph(quoinex.convertToStockStats(), False)


