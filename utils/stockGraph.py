import stockstats as stss
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc

import stockstats as stss
import pandas as pd
import numpy
import os


#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../7201.csv"))

#各パラメータ初期化
stock.get('macd')
stock.get('macds')
stock.get('macdh')
stock.get('rsi_6') #ワーニングが出るが気にしない
stock.get('rsi_12') #ワーニングが出るが気にしない
stock.get('boll_ub') #ボリンジャー
stock.get('boll_lb') #ボリンジャー
stock.get('tr')
stock.get('atr')
stock.get('kdjk')
stock.get('kdjd')
stock.get('kdjj')


openList = stock.as_matrix(columns=['open'])
closeList = stock.as_matrix(columns=['close'])
rsi6List = stock.as_matrix(columns=['rsi_6'])
rsi12List = stock.as_matrix(columns=['rsi_12'])
macdList = stock.as_matrix(columns=['macd'])
macdSignalList = stock.as_matrix(columns=['macds'])
macdHistList = stock.as_matrix(columns=['macdh'])
volumeList = stock.as_matrix(columns=['volume'])
bollLBList = stock.as_matrix(columns=['boll_lb'])
bollUBList = stock.as_matrix(columns=['boll_ub'])
trList = stock.as_matrix(columns=['tr'])
atrList = stock.as_matrix(columns=['atr'])
kdjkList = stock.as_matrix(columns=['kdjk'])
kdjdList = stock.as_matrix(columns=['kdjd'])
kdjjList = stock.as_matrix(columns=['kdjj'])

START_POS = 420

closeList = closeList[START_POS:len(closeList)]
rsi6List = rsi6List[START_POS:len(rsi6List)]
rsi12List = rsi12List[START_POS:len(rsi12List)]
macdList = macdList[START_POS:len(macdList)]
macdSignalList = macdSignalList[START_POS:len(macdSignalList)]
macdHistList = macdHistList[START_POS:len(macdHistList)]
volumeList = volumeList[START_POS:len(volumeList)]
bollLBList = bollLBList[START_POS:len(bollLBList)]
bollUBList = bollUBList[START_POS:len(bollUBList)]
trList = trList[START_POS:len(trList)]
atrList = atrList[START_POS:len(atrList)]
kdjkList = kdjkList[START_POS:len(kdjkList)]
kdjdList = kdjdList[START_POS:len(kdjdList)]
kdjjList = kdjjList[START_POS:len(kdjjList)]



#日経平均
nikkeiStock = stss.StockDataFrame().retype(pd.read_csv("../7201.csv"))
nCloseList = nikkeiStock.as_matrix(columns=['close'])

nCloseList = nCloseList[START_POS:len(nCloseList)-1]



if __name__ == '__main__':

    # plot graph
    fig = plt.figure(figsize=(10, 5))
    plt.title('Stock Graph', fontsize=10)
    plt.xlabel('x', fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # グラフ用
    graphData = numpy.array(stock.as_matrix(columns=['open', 'high', 'low', 'close']), dtype='float')

    #一つ目
    ax1 = fig.add_subplot(1,1,1)

    print(graphData[START_POS:len(graphData)])
    open_ = graphData[START_POS:len(graphData), 0]
    high_ = graphData[START_POS:len(graphData), 1]
    low_ = graphData[START_POS:len(graphData), 2]
    close_ = graphData[START_POS:len(graphData), 3]
    candlestick2_ohlc(ax1, open_, high_, low_, close_, colorup="b", width=0.5, colordown="r")

    # p6, = ax1.plot(bollUBList, label=r'bollu', color='black')

    #2つ目
    ax2 = ax1.twinx()
    ax2.set_ylabel('stochastic')
    p3, = ax2.plot(kdjkList, label=r'stochastic', color='orange')
    p5, = ax2.plot(kdjdList, label=r'stochastic', color='pink')
    p6, = ax2.plot(kdjjList, label=r'stochastic', color='red')
    #
    # plt.legend([p3, p5], ["rsi6", "rsi12"], loc=r'upper left')

    #3つ目
    # ax3 = fig.add_subplot(2,1,2)
    # p4, = ax3.plot(macdHistList, color='green')
    # p6, = ax3.plot(macdSignalList, color='purple')


    # plt.legend([p1, p2, p3], ["rsi", "macd", "close"])
    # plt.legend([p4], ["atr"], loc=r'upper left')

    if(os.path.exists("../figures") != True):
        os.mkdir("../figures")

    plt.savefig("../figures/candle.jpg", format="jpg", dpi=80)


    # plt.show()
