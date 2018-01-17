import numpy
import stockstats
import pandas

"""
stockstatsフォーマットにされているデータからCloseを取り出し、
t+1のcloseが下がったor同額:0、上がった:1

Returns:
    float formated numpy array.

"""
def data_updown(stock):
    # [n,1]のデータ
    allDataY = stock.as_matrix(columns=['close'])

    newY = []
    for i in range(allDataY.shape[0] - 1):
        upDown = 0
        if(allDataY[i + 1][0] > allDataY[i][0]):
            upDown = 1

        # []で囲まないと1次元配列になってしまう。
        newY.append([upDown])

    return numpy.array(newY, dtype='float')



"""
上記、stockではなく、arrayが渡ってくる場合はこちらを使用。
"""
def data_updownArray(dataArray):
    newY = []
    for i in range(dataArray.shape[0] - 1):
        upDown = 0
        if(dataArray[i + 1][0] > dataArray[i][0]):
            upDown = 1

        # []で囲まないと1次元配列になってしまう。
        newY.append([upDown])

    return numpy.array(newY, dtype='float')

"""
TODO: 上記、下がる、同額、上がるの三つにする
"""
def data_updownMarix(dataArray):
    newY = []
    for i in range(dataArray.shape[0] - 1):
        upDown = 0
        if(dataArray[i + 1][0] > dataArray[i][0]):
            upDown = 1

        # []で囲まないと1次元配列になってしまう。
        newY.append([upDown])

    return numpy.array(newY, dtype='float')



"""
2次元の
[[0,0,0],[0,1,0],[0,0,1] ... ]
のデータを
1次元に直す。
0: 下がる
1: 同期
2: 上がる

Returns:
    float formated numpy array.

"""
def convert_updown_toGraph(upDown):
    graphData = []
    for i in range(upDown.shape[0]):
        downFlg = upDown[i,0]
        sameFlg = upDown[i,1]
        upFlg = upDown[i,2]
        if(downFlg > 0.5):
            graphData.append(0)
        elif (sameFlg > 0.5):
            graphData.append(1)
        elif(upFlg > 0.5):
            graphData.append(2)

if __name__ == '__main__':
    stock = stockstats.StockDataFrame().retype(pandas.read_csv("../3632.csv"))
    print(data_updown(stock))
