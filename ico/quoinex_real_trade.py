from ico.quoinex_trade import QuoinexController
from ico.bit_buysell_logic import BitSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    quoinex = QuoinexController(key="", secret="")
    # quoinex.initGraph()

    bitsignal = BitSignalFinder(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])

    index=0
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

        bitsignal.update(quoinex._tickList, stockstatsClass)
        [buyOrderId, lossCutPrice] = bitsignal.decideLossCut()
        buyPrice = bitsignal.buySignal()
        sellPrice = bitsignal.sellSignal()

        if(buyOrderId != None and lossCutPrice > 0):
            quoinex.cancelOrder(buyOrderId)
            buyPrice = lossCutPrice

        if(buyPrice > 0):
            # orderId = quoinex.orderCoinRequest("buy", buyPrice, bitsignal._coinAmount)
            orderId = "buyxxxxx"
            bitsignal.updateStatus("buy", orderId)

        if(sellPrice > 0):
            # orderId = quoinex.orderCoinRequest("sell", sellPrice, bitsignal._coinAmount)
            orderId = "sellxxxxx"
            bitsignal.updateStatus("sell", orderId)


        quoinex.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
