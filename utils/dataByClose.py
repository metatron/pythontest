import numpy
import stockstats
import pandas


"""
stockstatsフォーマットにされているデータからCloseを取り出し、
[[close[t-1], close[t]],
 [close[t], close[t+1]],
...
 [close[t-n], close[t]]]
のフォーマットに変形する。

Returns:
    float formated numpy array.
    
"""
def data_by_close(stock):
    #[n,1]のデータ
    allDataY = stock.as_matrix(columns=['close'])

    newY=[]
    for i in range(allDataY.shape[0]-1):
        newY.append([allDataY[i][0], allDataY[i+1][0]])

    return numpy.array(newY, dtype='float')



if __name__ == '__main__':
    stock = stockstats.StockDataFrame().retype(pandas.read_csv("../3632.csv"))
    data_by_close(stock)
