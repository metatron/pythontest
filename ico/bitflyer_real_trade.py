from ico.bitflyer_trade import BitFlyerController
from ico.bit_buysell_logic import BitSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    bitflyer = BitFlyerController(key="", secret="")
    # bitflyer.initGraph()

    bitsignal = BitSignalFinder(bitflyer._tickList, bitflyer._candleStats, [0.0015, 0.0014])

    index=0
    while(index<10):
        bitflyer.getTickData()
        stockstatsClass = bitflyer.convertToStockStats()
        print(bitflyer._tickList[-1])

        bitsignal.update(bitflyer._tickList, stockstatsClass)
        [buyOrderId, lossCutPrice] = bitsignal.decideLossCut()
        [buyPrice] = bitsignal.buySignal()
        [sellPrice] = bitsignal.sellSignal()

        if(buyPrice > 0):
            bitsignal.updateStatus("buy", buyPrice)

        if(sellPrice > 0):
            bitsignal.updateStatus("sell", sellPrice)

        bitflyer.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
