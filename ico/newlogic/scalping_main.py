from ico.quoinex_trade import QuoinexController
from ico.newlogic.scalping_logic import ScalpingLogic
import pandas as pd
import numpy as np
import time


MAX_RETRY_COUNT = 10

#値段を変更してみる際はこの回数リトライしていること
UPDATEPRICE_RETRY_COUNT = 6

if __name__ == '__main__':
    quoinex = QuoinexController(key="", secret="")
    # quoinex.initGraph()

    simplesingal = ScalpingLogic(quoinex._tickList, quoinex._candleStats, [0.0, 0.0])
    # simplesingal._minEarn = 200.0
    simplesingal._coinAmount = 0.001

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

        simplesingal.update(quoinex._tickList, stockstatsClass)

        [buyNum, sellNum, aVec, buyPercent] = simplesingal.getBuyInfo(quoinex.getExecutions(sec=60, limit=100))
        print("buyNum:{}, sellNum:{}, crntPrice:{}, aVec:{}, buyPercent:{}".format(buyNum, sellNum, simplesingal.crntPrice, aVec, buyPercent))

        #近似値グラフ化
        #simplesingal.plotToKinjichi()

        buyFlg = False
        sellFlg = False
        if(simplesingal.getWaitingForRequest() == False):
            buyFlg = simplesingal.checkBuyInfo(buyNum, sellNum, aVec, buyPercent)
            sellFlg = simplesingal.checkSellInfo(buyNum, sellNum, aVec, buyPercent)

        if(buyFlg):
            side = "buy"
            print("****Bought Price:{}".format(simplesingal._buyPrice))
            crntOrderId = quoinex.orderCoinRequest(side, simplesingal._buyPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)
            simplesingal.setWaitingForRequest(True)

        if(sellFlg):
            side = "sell"
            print("****Sold crntPrice:{}, netEarned:{}".format(simplesingal.crntPrice, simplesingal.netEarned))
            crntOrderId = quoinex.orderCoinRequest(side, simplesingal._sellPrice, simplesingal._coinAmount)
            simplesingal.updateStatus(side, crntOrderId)
            simplesingal.setWaitingForRequest(True)

        if(crntOrderId != ""):
            status = quoinex.checkOrder(crntOrderId)
            if(status == "filled"):
                simplesingal.setWaitingForRequest(False)
                if(side == "sell"):
                    simplesingal.resetParamsForBuy()
                crntOrderId = ""
                side = ""
                retryCount = 0
            elif(status == "live"):
                retryCount += 1

                #途中で値段が下がった場合
                if(simplesingal.checkCancelInfo(buyNum, sellNum, aVec, buyPercent)):
                    quoinex.cancelOrder(crntOrderId)
                    print("CANCELED BUY ORDER 2! {} orderId:{}".format(simplesingal.crntTimeSec, crntOrderId))
                    simplesingal.resetParamsForBuy()
                    simplesingal.setWaitingForRequest(False)
                    crntOrderId = ""
                    side = ""
                    retryCount = 0
                #オーダーの値段変更
                elif(retryCount >= UPDATEPRICE_RETRY_COUNT):
                    updatedPrice = simplesingal.getUpdatedPrice()
                    if(updatedPrice > 0 and crntOrderId != ""):
                        print("CHANGING ORDER PRICE! orderId:{}, price:{}".format(crntOrderId, updatedPrice))
                        quoinex.updateOrder(crntOrderId, updatedPrice, simplesingal._coinAmount)



            if(retryCount >= MAX_RETRY_COUNT):
                # sellは絶対キャンセルしない。
                if(side == "buy" and status != "filled"):
                    quoinex.cancelOrder(crntOrderId)
                    print("CANCELED BUY ORDER 1! {} orderId:{}".format(simplesingal.crntTimeSec, crntOrderId))
                    simplesingal.resetParamsForBuy()
                    simplesingal.setWaitingForRequest(False)
                    crntOrderId = ""
                    side = ""
                    retryCount = 0

        randWait = np.random.randint(2, 3, dtype="int")
        time.sleep(int(randWait))
