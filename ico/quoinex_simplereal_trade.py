from ico.quoinex_trade import QuoinexController
from ico.simple_buysell_logic import SimpleSignalFinder
import pandas as pd
import numpy as np
import time


MAX_RETRY_COUNT = 20

if __name__ == '__main__':
    quoinex = QuoinexController(key="", secret="")
    quoinex.initGraph()

    simplesingal = SimpleSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    index=0
    crntOrderId = ""
    side = ""
    retryCount = 0
    while(index<10):
        try:
            quoinex.getTickData()
        except Exception as e:
            print("Error On GettingTickData: " + str(e))

            randWait = np.random.randint(1, 3, dtype="int")
            time.sleep(int(randWait))

            index += 1
            continue

        stockstatsClass = quoinex.convertToStockStats()
        print(quoinex._tickList[-1])

        simplesingal.update(quoinex._tickList, stockstatsClass)
        # simplesingal.decideLossCut()
        buyPrice = simplesingal.buySignal()
        sellPrice = simplesingal.sellSignal()
        simplesingal._checkDeadXed_MacdS()

        if(buyPrice > 0):
            side = "buy"
            crntOrderId = quoinex.orderCoinRequest(side, buyPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)

        if(sellPrice > 0):
            side = "sell"
            crntOrderId = quoinex.orderCoinRequest(side, sellPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)

        if(crntOrderId != ""):
            status = quoinex.checkOrder(crntOrderId)
            if(status == "filled"):
                if(side == "sell"):
                    simplesingal.resetParamsForBuy()
                crntOrderId = ""
                side = ""
                retryCount = 0
            elif(status == "live"):
                retryCount += 1

            if(retryCount >= MAX_RETRY_COUNT):
                # sellは絶対キャンセルしない。
                if(side == "buy"):
                    quoinex.cancelOrder(crntOrderId)
                    print("CANCELED BUY ORDER! {} orderId:{}".format(simplesingal.crntTimeSec, crntOrderId))
                    simplesingal.resetParamsForBuy()
                    crntOrderId = ""
                    side = ""
                    retryCount = 0




        quoinex.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
