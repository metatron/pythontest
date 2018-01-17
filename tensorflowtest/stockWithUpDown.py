# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/
# https://qiita.com/rakichiki/items/a514f3a4f3e979ace3c9

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM, Embedding, Conv1D, Flatten
from keras.optimizers import RMSprop, SGD, Adam
from keras.models import load_model
from pathlib import Path


import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd

from utils import addColumn, dataByClose, dataUpDown

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

from keras.layers.advanced_activations import LeakyReLU


#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../7201.csv"))

#各パラメータ初期化
stock.get('macd')
stock.get('rsi_6') #ワーニングが出るが気にしない

#[close[t-1],close[t]...のデータを作成
allDataCloseTime = dataByClose.data_by_close(stock)

# ノーマライズは一気にやってしまう。
scaler = MinMaxScaler(feature_range=(0, 1))
allDataNormalized = scaler.fit_transform(allDataCloseTime)


#closeデータ取得
allClose = np.array(stock.as_matrix(columns=['close']), dtype ='float')
closeScaler = MinMaxScaler(feature_range=(0, 1))
allCloseNormalized = closeScaler.fit_transform(allClose)


#volumeデータ取得
allVolume = np.array(stock.as_matrix(columns=['volume']), dtype ='float')
volumeScaler = MinMaxScaler(feature_range=(0, 1))
allVolumeNormalized = volumeScaler.fit_transform(allVolume)


#Rsiデータ取得
allRsi  = np.array(stock.as_matrix(columns=['rsi_6']), dtype ='float')
#[0] = NaN
allRsi[0] = 0
rsiScaler = MinMaxScaler(feature_range=(0, 1))
allRsiNormalized = rsiScaler.fit_transform(allRsi)


#macdデータ取得
allMacd  = np.array(stock.as_matrix(columns=['macd']), dtype ='float')
macdScaler = MinMaxScaler(feature_range=(0, 1))
allMacdNormalized = macdScaler.fit_transform(allMacd)


#上がった下がったデータ
allDataUpDown = dataUpDown.data_updown(stock)


#データを全てくっつける (close(t), close(t+1), rsi, macd) -> 成功
# allData = addColumn.add_column(allDataNormalized, allRsiNormalized[:len(allRsiNormalized)-1])
# allData = addColumn.add_column(allData, allMacdNormalized[:len(allMacdNormalized)-1])

#close, volume, rsi
allData = addColumn.add_column(allCloseNormalized, allVolumeNormalized)
allData = addColumn.add_column(allData, allRsiNormalized)
allData = addColumn.add_column(allData, allMacdNormalized)

print(allData.shape)
print(allDataUpDown.shape)


TRAINING_MAX_POS = 200
TESTING_MAX_POS = TRAINING_MAX_POS + 46


# 始値を入力値、上がり下がりを学習値としてデータ作成
trainX = allData[:TRAINING_MAX_POS]
trainY = allDataUpDown[:TRAINING_MAX_POS]

trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

#テストデータ作成
testX = allData[TRAINING_MAX_POS:TESTING_MAX_POS]
testY = allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS]

print(allDataCloseTime[TRAINING_MAX_POS:TESTING_MAX_POS])

testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

leaky_relu = LeakyReLU()


model = Sequential()

my_file = Path('cnn_model.h5')
if my_file.is_file():
    model = load_model('cnn_model.h5')
else:
    #filter: 出力、kernel_size: 各filterの長さ
    model.add(Conv1D(filters=20, kernel_size=trainX.shape[1], padding='same', input_shape=(1,trainX.shape[2])))
    model.add(Flatten())
    model.add(Dense(10))
    model.add(Dropout(0.1))
    # 最終出力次元
    model.add(Dense(1, activation='sigmoid'))

    # sgd = SGD(lr=0.1)
    # model.compile(loss='mean_squared_error', optimizer=sgd)

    model.summary()


    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    model.fit(trainX, trainY, epochs=50, batch_size=1)

    # save keras model
    model.save('cnn_model.h5')

# make predictions
trainPredict = model.predict_proba(testX)

# predictedY = scaler.inverse_transform(trainPredict)
resultSum = addColumn.add_column(trainPredict,testY)
print(resultSum)

#plot graph
plt.figure(figsize=(20, 5))
plt.title('Predict future values for time sequences', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.ylabel('y', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

#plt.plot(datasetY)
p1, = plt.plot(trainPredict)
p2, = plt.plot(testY)# [:,0])

plt.legend([p1, p2], ["trainPredict", "originalY"])

plt.show()
