from ico.bitflyer_trade import BitFlyerController
from ico.bit_buysell_logic import BitSignalFinder
import pandas as pd
import numpy as np
import time


if __name__ == '__main__':
    bitflyer = BitFlyerController()
    # bitflyer.initGraph()

    bitsignal = BitSignalFinder(bitflyer._tickList, bitflyer._candleStats)

    tickFilePath = "./csv/tick_201802281428_BTC_JPY.csv"
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

        print(bitflyer._tickList[-1],bitsignal._getBandBolaRatio())

        # index += 1
        # randWait = np.random.randint(1, 3, dtype="int")
        # time.sleep(int(randWait))

    print("total Earned:{}".format(bitsignal._totalEarned))
    bitflyer.initGraph()
    bitflyer.makeGraph(bitflyer.convertToStockStats(), False)

