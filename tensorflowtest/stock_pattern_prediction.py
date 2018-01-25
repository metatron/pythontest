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

from utils import addColumn, dataByClose, dataUpDown, data_converter

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

from keras.layers.advanced_activations import LeakyReLU
import os
from pathlib import Path

import tensorflow as tf

# 乱数シード固定（macdで調整）
# RAND_SEED = 777 #日産
RAND_SEED = 778 #日産 2018/01/15更新

np.random.seed(RAND_SEED)
tf.set_random_seed(RAND_SEED)


#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../7201.csv")) #日産
stock_nikkei = stss.StockDataFrame().retype(pd.read_csv("../NI225.csv")) #日経
stock_toyota = stss.StockDataFrame().retype(pd.read_csv("../7203.csv")) #トヨタ

# グラフ用
graphData = np.array(stock.as_matrix(columns=['open', 'high', 'low', 'close']), dtype ='float')

NUM_OF_TEST = 46
TRAINING_MAX_POS = graphData.shape[0] - NUM_OF_TEST
TESTING_MAX_POS = graphData.shape[0]

print(graphData[TRAINING_MAX_POS:TESTING_MAX_POS])

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



#open, closeデータ取得
allOpenClose = np.array(stock.as_matrix(columns=['open', 'close']), dtype ='float')
closeScaler = MinMaxScaler(feature_range=(0, 1))
allOpenCloseNormalized = closeScaler.fit_transform(allOpenClose)

allOpen = allOpenClose[:,0].reshape(allOpenClose.shape[0],1)
allOpenNormalized = allOpenCloseNormalized[:,0].reshape(allOpenClose.shape[0],1)

allClose = allOpenClose[:,1].reshape(allOpenClose.shape[0],1)
allCloseNormalized = allOpenCloseNormalized[:,1].reshape(allOpenClose.shape[0],1)


allHighLow = np.array(stock.as_matrix(columns=['high', 'low']), dtype ='float')
allHighLowNormalized = closeScaler.fit_transform(allHighLow)

allHighNormalized = allHighLowNormalized[:,0].reshape(allHighLow.shape[0],1)
allLowNormalized = allHighLowNormalized[:,1].reshape(allHighLow.shape[0],1)


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

#macdHist
allMacdH  = np.array(stock.as_matrix(columns=['macdh']), dtype ='float')
macdHScaler = MinMaxScaler(feature_range=(0, 1))
allMacdHNormalized = macdHScaler.fit_transform(allMacdH)

#macdSig
allMacdS  = np.array(stock.as_matrix(columns=['macds']), dtype ='float')
macdSScaler = MinMaxScaler(feature_range=(0, 1))
allMacdSNormalized = macdSScaler.fit_transform(allMacdS)

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


# 日経平均取り込み
allNikkeiOpen  = np.array(stock_nikkei.as_matrix(columns=['open']), dtype ='float')
nikkeiOpenScaler = MinMaxScaler(feature_range=(0, 1))
allNikkeiOpenNormalized = nikkeiOpenScaler.fit_transform(allNikkeiOpen)

# トヨタ取り込み
allToyotaOpen  = np.array(stock_toyota.as_matrix(columns=['open']), dtype ='float')
toyotaOpenScaler = MinMaxScaler(feature_range=(0, 1))
allToyotaOpenNormalized = toyotaOpenScaler.fit_transform(allToyotaOpen)



#上がった下がったデータ
# allDataUpDown = dataUpDown.data_closeUpDown(stock)
allDataUpDown = dataUpDown.data_openCloseUpDwn(stock)
# allDataUpDown = dataUpDown.data_openCloseUpDwn2(stock)


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

#データをくっつける2（open(t), close(t), high(t), low(t), open(t+1))
# allOpenT1 = allOpenNormalized[1:]
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)-1], allHighLowNormalized[:len(allMacdSNormalized)-1])
# allData = addColumn.add_column(allData, allOpenT1)
# dataArray.append([allData,"NoParam"])



"""
=== 自作パラメータ ===
"""
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdNormalized[:len(allMacdNormalized)])
# allData = addColumn.add_column(allData, allTrNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Macd&Tr"])

# macdH
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdHNormalized[:len(allMacdHNormalized)])
# dataArray.append([allData,"MacdHist"])

# macdS
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdSNormalized[:len(allMacdSNormalized)])
# dataArray.append([allData,"MacdSig"])

# macd & rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdNormalized[:len(allMacdNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"Macd&Rsi"])


# macds & rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdSNormalized[:len(allMacdSNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"MacdS&Rsi"])


# macdh & rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdHNormalized[:len(allMacdHNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"MacdH&Rsi"])


# macd & rsi & Vol & Tr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allRsiNormalized[:len(allRsiNormalized)])
# allData = addColumn.add_column(allData, allVolumeNormalized[:len(allVolumeNormalized)])
# allData = addColumn.add_column(allData, allVolumeNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Rsi&Vol&Tr"])


# macds & nikkei & Toyota
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdSNormalized[:len(allMacdSNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# allData = addColumn.add_column(allData, allNikkeiOpenNormalized[:len(allNikkeiOpenNormalized)])
# allData = addColumn.add_column(allData, allToyotaOpenNormalized[:len(allToyotaOpenNormalized)])
# dataArray.append([allData,"MacdS&Rsi&Nikkei&Toyota"])


# macds & toyota & rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdSNormalized[:len(allMacdSNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# allData = addColumn.add_column(allData, allToyotaOpenNormalized[:len(allToyotaOpenNormalized)])
# dataArray.append([allData,"MacdS&Toyota&Rsi_2"])

# close, open, high, low, rsi -> いい感じ
allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
dataArray.append([allData,"Open&Close&High&Low&Rsi", None, None])

# close, open, high, low, macdh -> いい感じ
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allMacdHNormalized[:len(allMacdHNormalized)])
# dataArray.append([allData,"Open&Close&High&Low&MacdH_lstm", None, None])

# close, open, high, low, macd, rsi -> いい感じ
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allMacdHNormalized[:len(allMacdHNormalized)])
# allData = addColumn.add_column(allData, allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_tanh_rmsprop", None, None]) # ->これが一番
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_relu_rmsprop", 'relu', None])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_elu_rmsprop", 'elu', None])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_softmax_rmsprop", 'softmax', None])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_selu_rmsprop", 'selu', None])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_sigmoid_rmsprop", 'sigmoid', None])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_tanh_adam", 'tanh', 'adam'])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_relu_adam", 'relu', 'adam'])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_elu_adam", 'elu', 'adam'])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_softmax_adam", 'softmax', 'adam'])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_selu_adam", 'selu', 'adam'])
# dataArray.append([allData,"Open&Close&High&Low&MacdH&Rsi_sigmoid_adam", 'sigmoid', 'adam'])



# close, open, high, low, toyota
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allToyotaOpenNormalized[:len(allToyotaOpenNormalized)])
# dataArray.append([allData,"Open&Close&High&Low&Toyota"])



"""
=== 各パラメター調査 ===
"""
# rsi
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allRsiNormalized[:len(allRsiNormalized)])
# dataArray.append([allData,"Rsi"])


# macd
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allMacdNormalized[:len(allMacdNormalized)])
# dataArray.append([allData,"Macd"])

# # atr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allAtrNormalized[:len(allAtrNormalized)])
# dataArray.append([allData,"Atr"])
#
#
# # tr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allTrNormalized[:len(allTrNormalized)])
# dataArray.append([allData,"Tr"])
#
#
# kdj
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allKdjNormalized[:len(allKdjNormalized)])
# dataArray.append([allData,"Kdj", None, None])
#
#
# # dma
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allDmaNormalized[:len(allDmaNormalized)])
# dataArray.append([allData,"Dma"])
#
#
# # adx
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allAdxNormalized[:len(allAdxNormalized)])
# dataArray.append([allData,"Adx"])
#
#
# # trix
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allTrxNormalized[:len(allTrxNormalized)])
# dataArray.append([allData,"Trix"])
#
#
# # wr
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allWr6Normalized[:len(allWr6Normalized)])
# dataArray.append([allData,"Wr"])
#
#
# # cci
# allData = addColumn.add_column(allOpenCloseNormalized[:len(allOpenCloseNormalized)], allHighLowNormalized[:len(allHighLowNormalized)])
# allData = addColumn.add_column(allData, allCciNormalized[:len(allCciNormalized)])
# dataArray.append([allData,"Cci"])


for i in range(len(dataArray)):
    data_ = dataArray[i][0]
    title = dataArray[i][1]
    activation = dataArray[i][2]
    if(activation == None):
        activation = 'tanh'

    optimizer = dataArray[i][3]
    if(optimizer == None):
        optimizer = 'rmsprop'

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
    spdClass = spd(trainX, trainY, testX, testY, False, activation, optimizer)
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

    #予測を1,0に変換
    updownPred = data_converter.convert_results_updown(trainPredict)
    # p4, = ax2.plot(updownPred, label=r'prediction', color='pink')

    #一番最後は予測できないのでとりあえず0を追加
    tmpArray = allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS]
    tmpArray = np.append(tmpArray, [0])
    tmpArray = tmpArray.reshape(len(tmpArray), 1)
    resArray = addColumn.add_column(trainPredict, tmpArray)
    resArray = addColumn.add_column(resArray, updownPred)
    print(resArray)

    plt.legend([p2, p3], ["prediction", "updown"], loc=r"upper left")

    if(os.path.exists("../figures") != True):
        os.mkdir("../figures")

    plt.savefig("../figures/" + title + ".jpg", format="jpg", dpi=80)

    # plt.show()

    del fig
    del spdClass
