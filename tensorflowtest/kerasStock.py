# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM
from keras.optimizers import RMSprop, SGD
from keras.models import load_model
from pathlib import Path


import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd

import utils.addColumn

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))
# print(stock.as_matrix(columns=['high','low','open','volume']))

#各パラメータ初期化
stock['macd']
stock['rsi_6']

allDataX = np.array(stock.as_matrix(columns=['open']), dtype='float')
allDataY = np.array(stock.as_matrix(columns=['close']), dtype='float')

allMacd  = np.array(stock.as_matrix(columns=['macd']), dtype ='float')
allRsi  = np.array(stock.as_matrix(columns=['rsi_6']), dtype ='float')
#[0] = NaN
allRsi[0] = 0


# ノーマライズは学習用、テスト用両方一気にやってしまわないといけない気がする。
scaler = MinMaxScaler(feature_range=(0, 1))
allDataNormalizedX = scaler.fit_transform(allDataX)
allDataNormalizedY = scaler.fit_transform(allDataY)

# 各パラメータは別でノーマライズ
macdScaler = MinMaxScaler(feature_range=(0, 1))
allMacdNormalized = macdScaler.fit_transform(allMacd)

rsiScaler = MinMaxScaler(feature_range=(0, 1))
allRsiNormalized = rsiScaler.fit_transform(allRsi)



# 始値を入力値、終値を学習値としてデータ作成
trainX = allDataNormalizedX[:150]
trainY = allDataNormalizedY[:150]

# datasetX = np.array(stock.as_matrix(columns=['open', 'macd'])[:100], dtype='float')
# datasetY = np.array(stock.as_matrix(columns=['close'])[:100], dtype='float')

# scaler = MinMaxScaler(feature_range=(0, 1))
# trainX = scaler.fit_transform(datasetX)
# trainY = scaler.fit_transform(datasetY)

# 各パラメータを追加
trainX = utils.addColumn.add_column(trainX, allMacdNormalized[:150])
trainX = utils.addColumn.add_column(trainX, allRsiNormalized[:150])

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

print(trainX)


#予想するデータを用意
testDatasetY = allDataY[150:250]
testX = allDataNormalizedX[150:250]
testY = allDataNormalizedY[150:250]

# testDatasetX = np.array(stock.as_matrix(columns=['open', 'macd'])[100:200], dtype='float')
# testDatasetY = np.array(stock.as_matrix(columns=['close'])[100:200], dtype='float')

# testX = scaler.fit_transform(testDatasetX)
# scaler.inverse_transformをする時何故か必要。。
# testY = scaler.fit_transform(testDatasetY)

# 各パラメータを追加
testX = utils.addColumn.add_column(testX, allMacdNormalized[150:250])
testX = utils.addColumn.add_column(testX, allRsiNormalized[150:250])

# reshape input to be [samples, time steps, features]
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

print(testX)

model = Sequential()

my_file = Path('lstm_model.h5')
if my_file.is_file():
    model = load_model('lstm_model.h5')
else:
    # 2つ以上のLSTMレイヤーを組み合わせる場合、一つ前のLSTMレイヤのreturn_sequences=Trueにする。
    model.add(LSTM(10,input_shape=(1,3),return_sequences=True))
    model.add(Dropout(0.1))
    model.add(LSTM(10))
    model.add(Dropout(0.1))
    model.add(Dense(1))

    # sgd = SGD(lr=0.1)
    model.compile(loss='mean_squared_error', optimizer='adam')

    model.fit(trainX, trainY, epochs=100, batch_size=2)

    # save keras model
    # model.save('lstm_model.h5')

# make predictions
#trainPredict = model.predict(trainX)
trainPredict = model.predict(testX)
predictedY = scaler.inverse_transform(trainPredict)
print(predictedY)

#plot graph
plt.figure(figsize=(20, 5))
plt.title('Predict future values for time sequences', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.ylabel('y', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

#plt.plot(datasetY)
p1, = plt.plot(testDatasetY)
p2, = plt.plot(predictedY)# [:,0])

plt.legend([p1, p2], ["testDatasetY", "predictedY"])

plt.show()
