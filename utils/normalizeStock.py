"""
一定間隔の合計でその間の株価を割る。

Returns:
    float formated numpy array.

"""
def normalize_stock(dataArray, numNormalize=5):
    for i in range(len(dataArray)-numNormalize):
        tmpStoreData = []
        #データを貯める
        if(i%numNormalize > 0):
            tmpStoreData.append(dataArray[i])
        #データがストアされており、一定期間貯めたらその区間の平均を求める
        elif(i%numNormalize == 0) and (len(tmpStoreData) > 0):
            print('test')


if __name__ == '__main__':
    stock = stockstats.StockDataFrame().retype(pandas.read_csv("../3632.csv"))
    print(data_updown(stock))
