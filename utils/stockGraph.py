import stockstats as stss
import pandas as pd
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd


#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))

#各パラメータ初期化
stock.get('macd')
stock.get('rsi_6') #ワーニングが出るが気にしない
stock.get('boll_ub') #ボリンジャー
stock.get('boll_lb') #ボリンジャー


openList = stock.as_matrix(columns=['open'])
closeList = stock.as_matrix(columns=['close'])
rsiList = stock.as_matrix(columns=['rsi_6'])
macdList = stock.as_matrix(columns=['macd'])
volumeList = stock.as_matrix(columns=['volume'])
bollLBList = stock.as_matrix(columns=['boll_lb'])
bollUBList = stock.as_matrix(columns=['boll_ub'])

closeList = closeList[200:len(closeList)-1]
rsiList = rsiList[200:len(rsiList)-1]
macdList = macdList[200:len(macdList)-1]
volumeList = volumeList[200:len(volumeList)-1]
bollLBList = bollLBList[200:len(bollLBList)-1]
bollUBList = bollUBList[200:len(bollUBList)-1]


if __name__ == '__main__':

    # plot graph
    fig = plt.figure(figsize=(10, 5))
    plt.title('Stock Graph', fontsize=10)
    plt.xlabel('x', fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    #一つ目
    ax1 = fig.add_subplot(1,1,1)
    ax1.set_ylabel('close')
    p1, = ax1.plot(closeList, label=r'close', color='blue')
    # p2, = ax1.plot(openList)

    #2つ目
    ax2 = ax1.twinx()
    ax2.set_ylabel('boll')
    p2, = ax2.plot(bollLBList, label=r'boll', color='orange')
    p3, = ax2.plot(bollUBList, color='green')

    #3つ目
    # ax3 = fig.add_subplot(2,1,2)
    # p3, = ax3.plot(closeList, color='green')


    # plt.legend([p1, p2, p3], ["rsi", "macd", "close"])
    plt.legend([p1, p2], ["close", "boll"])

    plt.show()
