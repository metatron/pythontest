# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/
# https://qiita.com/rakichiki/items/a514f3a4f3e979ace3c9

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM, Embedding, Conv1D, Flatten, MaxPooling1D
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

TRAINING_MAX_POS = 200
TESTING_MAX_POS = TRAINING_MAX_POS + 48

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


#上がった下がったデータ
allDataUpDown = dataUpDown.data_closeUpDown(stock)


#データを全てくっつける (close(t), close(t+1), rsi, macd) -> 成功
# allData = addColumn.add_column(allDataNormalized, allRsiNormalized[:len(allRsiNormalized)-1])
# allData = addColumn.add_column(allData, allMacdNormalized[:len(allMacdNormalized)-1])

#close, tr, rsi, macd
allData = addColumn.add_column(allCloseNormalized, allAtrNormalized)
allData = addColumn.add_column(allData, allRsiNormalized)
allData = addColumn.add_column(allData, allMacdNormalized)

print(allData.shape)
print(allDataUpDown.shape)



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
    model.add(Conv1D(filters=40, kernel_size=trainX.shape[1], padding='same', input_shape=(1,trainX.shape[2])))
    # model.add(LSTM(20, return_sequences=True, activation='relu'))
    model.add(Dense(20, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dropout(0.2))
    # 最終出力次元
    model.add(Dense(1, activation='relu'))

    # sgd = SGD(lr=0.1)
    # model.compile(loss='mean_squared_error', optimizer=sgd)

    model.summary()


    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    model.fit(trainX, trainY, epochs=50, batch_size=1)

    # save keras model
    model.save('cnn_model.h5')

# make predictions
trainPredict = model.predict(testX)

#予測を0,1でスケーリングしてみる？->微妙。。
# resultScaler = MinMaxScaler(feature_range=(0, 1))
# trainPredict = resultScaler.fit_transform(trainPredict)

# 結果を見るためにデータ用意
checkData = allClose[TRAINING_MAX_POS:TESTING_MAX_POS]
checkData = addColumn.add_column(checkData,trainPredict)
# checkData = addColumn.add_column(checkData,testY)
checkData.dtype=float
print(checkData)

#plot graph
fig = plt.figure(figsize=(10, 5))
plt.title('Prediction Graph', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

# 一つ目
ax1 = fig.add_subplot(1, 1, 1)
ax1.set_ylabel('close')
p1, = ax1.plot(allCloseNormalized[TRAINING_MAX_POS:TESTING_MAX_POS], label=r'close', color='blue')
p4, = ax1.plot(allRsiNormalized[TRAINING_MAX_POS:TESTING_MAX_POS], label=r'rsi', color='black')

# 2つ目
ax2 = ax1.twinx()
ax2.set_ylabel('prediction')
p2, = ax2.plot(trainPredict, label=r'prediction', color='orange')
# 3つ目
p3, = ax2.plot(allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS], color='green')

# 3つ目
# ax3 = fig.add_subplot(2,1,2)
# p3, = ax3.plot(closeList, color='green')


# plt.legend([p1, p2, p3], ["rsi", "macd", "close"])
plt.legend([p1, p2, p3, p4], ["close", "prediction", "updown", "rsi"], loc=r"upper left")

plt.show()
