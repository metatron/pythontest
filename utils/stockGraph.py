import stockstats as stss
import pandas as pd
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd


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

START_POS = 150

closeList = closeList[START_POS:len(closeList)-1]
rsi6List = rsi6List[START_POS:len(rsi6List)-1]
rsi12List = rsi12List[START_POS:len(rsi12List)-1]
macdList = macdList[START_POS:len(macdList)-1]
macdSignalList = macdSignalList[START_POS:len(macdSignalList)-1]
macdHistList = macdHistList[START_POS:len(macdHistList)-1]
volumeList = volumeList[START_POS:len(volumeList)-1]
bollLBList = bollLBList[START_POS:len(bollLBList)-1]
bollUBList = bollUBList[START_POS:len(bollUBList)-1]
trList = trList[START_POS:len(trList)-1]
atrList = atrList[START_POS:len(atrList)-1]



#日経平均
nikkeiStock = stss.StockDataFrame().retype(pd.read_csv("../NI225.csv"))
nCloseList = nikkeiStock.as_matrix(columns=['close'])

nCloseList = nCloseList[START_POS:len(nCloseList)-1]



if __name__ == '__main__':

    # plot graph
    fig = plt.figure(figsize=(10, 5))
    plt.title('Stock Graph', fontsize=10)
    plt.xlabel('x', fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    #一つ目
    ax1 = fig.add_subplot(2,1,1)
    ax1.set_ylabel('close')
    p1, = ax1.plot(closeList, label=r'close', color='blue')
    # p6, = ax1.plot(bollUBList, label=r'bollu', color='black')

    #2つ目
    ax2 = ax1.twinx()
    ax2.set_ylabel('rsi')
    p3, = ax2.plot(rsi6List, label=r'rsi6', color='orange')
    p5, = ax2.plot(rsi12List, label=r'rsi12', color='pink')

    plt.legend([p1, p3, p5], ["close", "rsi6", "rsi12"], loc=r'upper left')

    #3つ目
    ax3 = fig.add_subplot(2,1,2)
    p4, = ax3.plot(macdHistList, color='green')
    p6, = ax3.plot(macdSignalList, color='purple')


    # plt.legend([p1, p2, p3], ["rsi", "macd", "close"])
    plt.legend([p4], ["atr"], loc=r'upper left')

    plt.show()
