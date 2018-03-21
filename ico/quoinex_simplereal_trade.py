from ico.quoinex_trade import QuoinexController
from ico.simple_buysell_logic import SimpleSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    quoinex = QuoinexController(key="", secret="")
    quoinex.initGraph()

    simplesingal = SimpleSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    index=0
    crntOrderId = ""
    side = ""
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
        [buyOrderId, lossCutPrice] = simplesingal.decideLossCut()
        buyPrice = simplesingal.buySignal()
        sellPrice = simplesingal.sellSignal()

        if(buyOrderId != None and lossCutPrice > 0):
            quoinex.cancelOrder(buyOrderId)
            buyPrice = lossCutPrice

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
            if(status == "filled" and side == "sell"):
                simplesingal.resetBuySellParams()
                crntOrderId = ""
                side = ""



        quoinex.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
