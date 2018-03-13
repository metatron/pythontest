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
        quoinex.getTickData()
        stockstatsClass = quoinex.convertToStockStats()
        print(quoinex._tickList[-1])

        bitsignal.update(quoinex._tickList, stockstatsClass)
        bitsignal.decideLossCut()
        bitsignal.buySignal()
        bitsignal.sellSignal()

        quoinex.writeTickList()

        # index += 1
        randWait = np.random.randint(1, 3, dtype="int")
        time.sleep(int(randWait))
