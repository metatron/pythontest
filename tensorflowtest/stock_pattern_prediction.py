# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/
# https://qiita.com/rakichiki/items/a514f3a4f3e979ace3c9

from predictionclass.stock_pattern_detector import StockPatternDetect as spd

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc
import stockstats as stss
import pandas as pd

from utils import addColumn, dataByClose, dataUpDown

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

from keras.layers.advanced_activations import LeakyReLU
import os
from pathlib import Path

import tensorflow as tf

# 乱数シード固定（macdで調整）
np.random.seed(777)
tf.set_random_seed(777)

TRAINING_MAX_POS = 200
TESTING_MAX_POS = TRAINING_MAX_POS + 49

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../7201.csv"))

#各パラメータ初期化
stock.get('macd')
stock.get('rsi_6') #ワーニングが出るが気にしない
stock.get('tr')
stock.get('atr')

#[close[t-1],close[t]...のデータを作成
allDataCloseTime = dataByClose.data_by_close(stock)

# ノーマライズは一気にやってしまう。
scaler = MinMaxScaler(feature_range=(0, 1))
allDataNormalized = scaler.fit_transform(allDataCloseTime)

# グラフ用
graphData = np.array(stock.as_matrix(columns=['open', 'high', 'low', 'close']), dtype ='float')


#open, closeデータ取得
allOpenClose = np.array(stock.as_matrix(columns=['open', 'close']), dtype ='float')
closeScaler = MinMaxScaler(feature_range=(0, 1))
allOpenCloseNormalized = closeScaler.fit_transform(allOpenClose)

allOpen = allOpenClose[:,0].reshape(allOpenClose.shape[0],1)
allOpenNormalized = allOpenCloseNormalized[:,0].reshape(allOpenClose.shape[0],1)

allClose = allOpenClose[:,1].reshape(allOpenClose.shape[0],1)
allCloseNormalized = allOpenCloseNormalized[:,1].reshape(allOpenClose.shape[0],1)

#volumeデータ取得
allVolume = np.array(stock.as_matrix(columns=['volume']), dtype ='float')
volumeScaler = MinMaxScaler(feature_range=(0, 1))
allVolumeNormalized = volumeScaler.fit_transform(allVolume)


#Rsiデータ取得
allRsi  = np.array(stock.as_matrix(columns=['rsi_6']), dtype ='float')
#[0] = NaN
allRsi[0] = 0
allRsi[1] = 0
rsiScaler = MinMaxScaler(feature_range=(0, 1))
allRsiNormalized = rsiScaler.fit_transform(allRsi)


#macdデータ取得
allMacd  = np.array(stock.as_matrix(columns=['macd']), dtype ='float')
macdScaler = MinMaxScaler(feature_range=(0, 1))
allMacdNormalized = macdScaler.fit_transform(allMacd)

#macdの差分取得
allMacdH  = np.array(stock.as_matrix(columns=['macdh']), dtype ='float')
allMacdS  = np.array(stock.as_matrix(columns=['macds']), dtype ='float')
allMacdDif = allMacdH - allMacdS
macdDifScaler = MinMaxScaler(feature_range=(0, 1))
allMacdDifNormalized = macdDifScaler.fit_transform(allMacdDif)

#trデータ取得
allTr  = np.array(stock.as_matrix(columns=['tr']), dtype ='float')
allTr[0] = 0
trScaler = MinMaxScaler(feature_range=(0, 1))
allTrNormalized = trScaler.fit_transform(allTr)


#atrデータ取得
allAtr  = np.array(stock.as_matrix(columns=['atr']), dtype ='float')
allAtr[0] = 0
atrScaler = MinMaxScaler(feature_range=(0, 1))
allAtrNormalized = atrScaler.fit_transform(allAtr)


#kdjデータ取得（Stochastic oscillator）
stock.get('kdjj')
allKdj  = np.array(stock.as_matrix(columns=['kdjj']), dtype ='float')
kdjScaler = MinMaxScaler(feature_range=(0, 1))
allKdjNormalized = kdjScaler.fit_transform(allKdj)


#dmaデータ取得（Different of Moving Average）
stock.get('dma')
allDma  = np.array(stock.as_matrix(columns=['dma']), dtype ='float')
dmaScaler = MinMaxScaler(feature_range=(0, 1))
allDmaNormalized = dmaScaler.fit_transform(allDma)


#adxデータ取得（Average Directional Movement Index）
stock.get('adx')
allAdx  = np.array(stock.as_matrix(columns=['adx']), dtype ='float')
allAdx[0] = 0
allAdx[1] = 0
adxScaler = MinMaxScaler(feature_range=(0, 1))
allAdxNormalized = adxScaler.fit_transform(allAdx)


#trixデータ取得（Average Directional Movement Index）
stock.get('trix')
allTrx  = np.array(stock.as_matrix(columns=['trix']), dtype ='float')
allTrx[0] = 0
trxScaler = MinMaxScaler(feature_range=(0, 1))
allTrxNormalized = trxScaler.fit_transform(allTrx)


#wrデータ取得（Williams Overbought）
stock.get('wr_6')
allWr6  = np.array(stock.as_matrix(columns=['wr_6']), dtype ='float')
wr6Scaler = MinMaxScaler(feature_range=(0, 1))
allWr6Normalized = wr6Scaler.fit_transform(allWr6)


#cciデータ取得（Commodity Channel Index）
stock.get('cci')
allCci  = np.array(stock.as_matrix(columns=['cci']), dtype ='float')
allCci[0] = 0
cciScaler = MinMaxScaler(feature_range=(0, 1))
allCciNormalized = wr6Scaler.fit_transform(allCci)



#上がった下がったデータ
# allDataUpDown = dataUpDown.data_closeUpDown(stock)
allDataUpDown = dataUpDown.data_openCloseUpDwn(stock)


# print(addColumn.add_column(allOpenClose[:len(allOpenClose)-1], allDataUpDown))

#どれがいいか総当たりを行う
dataArray = []

"""
=== 理想系パラメータ ===
"""
#データを全てくっつける (close(t), close(t+1), rsi, macd) -> 成功
# allData = addColumn.add_column(allDataNormalized, allRsiNormalized[:len(allRsiNormalized)-1])
# allData = addColumn.add_column(allData, allMacdNormalized[:len(allMacdNormalized)-1])

#データをくっつける（open(t), close(t), open(t+1))
# allOpenT1 = allOpenNormalized[1:]
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)-1], allOpenT1)
# dataArray.append([allData,"NoParam"])


"""
=== 自作パラメータ ===
"""
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdNormalized[:len(allMacdNormalized)])
# allData = addColumn.add_column(allData, allTrNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Macd&Tr"])

# macdh - macds
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdDifNormalized[:len(allMacdDifNormalized)])
# dataArray.append([allData,"MacdHist-MacdSignal"])

# macd & rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allRsiNormalized[:len(allRsiNormalized)])
# allData = addColumn.add_column(allData, allMacdNormalized[:len(allMacdNormalized)])
# allData = addColumn.add_column(allData, allVolumeNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Rsi&Macd&Tr"])




"""
=== 各パラメター調査 ===
"""
# rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"Rsi"])


# macd
allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdNormalized[:len(allMacdNormalized)])
dataArray.append([allData,"Macd"])

# # atr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allAtrNormalized[:len(allAtrNormalized)])
# dataArray.append([allData,"Atr"])
#
#
# # tr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allTrNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Tr"])
#
#
# # kdj
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allKdjNormalized[:len(allKdjNormalized)])
# dataArray.append([allData,"Kdj"])
#
#
# # dma
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allDmaNormalized[:len(allDmaNormalized)])
# dataArray.append([allData,"Dma"])
#
#
# # adx
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allAdxNormalized[:len(allAdxNormalized)])
# dataArray.append([allData,"Adx"])
#
#
# # trix
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allTrxNormalized[:len(allTrxNormalized)])
# dataArray.append([allData,"Trix"])
#
#
# # wr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allWr6Normalized[:len(allWr6Normalized)])
# dataArray.append([allData,"Wr"])
#
#
# # cci
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allCciNormalized[:len(allCciNormalized)])
# dataArray.append([allData,"Cci"])


for i in range(len(dataArray)):
    data_ = dataArray[i][0]
    title = dataArray[i][1]

    print('===================== ' + title + ' ===================== ')

    # 始値を入力値、上がり下がりを学習値としてデータ作成
    trainX = data_[:TRAINING_MAX_POS]
    trainY = allDataUpDown[:TRAINING_MAX_POS]

    trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

    #テストデータ作成
    testX = data_[TRAINING_MAX_POS:TESTING_MAX_POS]
    testY = allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS]

    testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

    #stock prediction
    spdClass = spd(trainX, trainY, testX, testY, False)
    trainPredict = spdClass.train_model()


    #plot graph
    fig = plt.figure(figsize=(10, 5))
    plt.title('Prediction Graph: ' + title, fontsize=10)
    plt.xlabel('x', fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    # 一つ目
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.set_ylabel('candle')
    # p1, = ax1.plot(allOpen[TRAINING_MAX_POS:TESTING_MAX_POS], label=r'open', color='blue')
    open_ = graphData[TRAINING_MAX_POS:TESTING_MAX_POS, 0]
    high_ = graphData[TRAINING_MAX_POS:TESTING_MAX_POS, 1]
    low_ = graphData[TRAINING_MAX_POS:TESTING_MAX_POS, 2]
    close_ = graphData[TRAINING_MAX_POS:TESTING_MAX_POS, 3]
    candlestick2_ohlc(ax1, open_, high_, low_, close_, colorup="b", width=0.5, colordown="r")

    print(graphData[TRAINING_MAX_POS:TESTING_MAX_POS])

    # 0,1でスケーリングして見る。。
    # predScaler = MinMaxScaler(feature_range=(0, 1))
    # trainPredict = predScaler.fit_transform(trainPredict)

    # 2つ目
    ax2 = ax1.twinx()
    ax2.set_ylabel('prediction')
    p2, = ax2.plot(trainPredict, label=r'prediction', color='orange')
    # 3つ目
    p3, = ax2.plot(allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS], color='green')
    # 0.5線
    middleLine = np.ones(len(allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS])+1)*0.5
    ax2.plot(middleLine, color='red')

    plt.legend([p2, p3], ["prediction", "updown"], loc=r"upper left")

    if(os.path.exists("../figures") != True):
        os.mkdir("../figures")

    plt.savefig("../figures/" + title + ".jpg", format="jpg", dpi=400)

    # plt.show()

    del fig
    del spdClass
