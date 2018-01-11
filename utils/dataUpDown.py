import numpy
import stockstats
import pandas

"""
stockstatsフォーマットにされているデータからCloseを取り出し、
t+1のcloseが下がった:[1,0,0]、同額:[0,1,0]、上がった:[0,0,1]

Returns:
    float formated numpy array.

"""
def data_updown(stock):
    # [n,1]のデータ
    allDataY = stock.as_matrix(columns=['close'])

    newY = []
    for i in range(allDataY.shape[0] - 1):
        upDown = [1,0,0]
        if(allDataY[i + 1][0] == allDataY[i][0]):
            upDown = [0,1,0]
        elif(allDataY[i + 1][0] > allDataY[i][0]):
            upDown = [0,0,1]

        # []で囲まないと1次元配列になってしまう。
        newY.append(upDown)

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
