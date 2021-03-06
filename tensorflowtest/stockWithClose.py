# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/
# http://dragstar.hatenablog.com/entry/2016/05/24/145543
# http://arkouji.cocolog-nifty.com/blog/2017/08/rnnlstm-0445.html

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

from utils import addColumn, dataByClose

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))

#各パラメータ初期化
stock.get('macd')
stock.get('rsi_6') #ワーニングが出るが気にしない

#[close[t-1],close[t]...のデータを作成
allDataXY = dataByClose.data_by_close(stock)
print(allDataXY)

allDataX = allDataXY[:,0].reshape(len(allDataXY[:,0]),1)
allDataY = allDataXY[:,1].reshape(len(allDataXY[:,1]),1)

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

TRAINING_MAX_POS = 200
TESTING_MAX_POS = TRAINING_MAX_POS + 46


# 始値を入力値、終値を学習値としてデータ作成
testDatasetY = allDataY[:TESTING_MAX_POS]
trainX = allDataNormalizedX[:TRAINING_MAX_POS]
trainY = allDataNormalizedY[:TRAINING_MAX_POS]

# 各パラメータを追加
# trainX = addColumn.add_column(trainX, allMacdNormalized[:TRAINING_MAX_POS])
# trainX = addColumn.add_column(trainX, allRsiNormalized[:TRAINING_MAX_POS])

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

print(trainX)


#予想するデータを用意
# testDatasetY = allDataY[TRAINING_MAX_POS:TESTING_MAX_POS]
testX = allDataNormalizedX[TRAINING_MAX_POS:TESTING_MAX_POS]
testY = allDataNormalizedY[TRAINING_MAX_POS:TESTING_MAX_POS]

# 各パラメータを追加
# testX = addColumn.add_column(testX, allMacdNormalized[TRAINING_MAX_POS:TESTING_MAX_POS])
# testX = addColumn.add_column(testX, allRsiNormalized[TRAINING_MAX_POS:TESTING_MAX_POS])

# reshape input to be [samples, time steps, features]
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

# print(testX)

model = Sequential()

my_file = Path('lstm_model.h5')
if my_file.is_file():
    model = load_model('lstm_model.h5')
else:
    # 2つ以上のLSTMレイヤーを組み合わせる場合、一つ前のLSTMレイヤのreturn_sequences=Trueにする。
    model.add(LSTM(20,input_shape=(1,1),return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(10))
    model.add(Dropout(0.2))
    model.add(Dense(5))
    model.add(Dense(1, activation='linear'))

    # sgd = SGD(lr=0.1)
    # model.compile(loss='mean_squared_error', optimizer=sgd)
    model.compile(loss='mean_squared_error', optimizer='adam', metrics=['accuracy'])

    model.fit(trainX, trainY, epochs=40, batch_size=2)

    # save keras model
    # model.save('lstm_model.h5')

# 予測インプット値の確認
# print(scaler.inverse_transform(testX[:,:,0]))

# make predictions
trainPredict = model.predict(trainX)
# trainPredict = model.predict(testX)
predictedY = scaler.inverse_transform(trainPredict)
print(testDatasetY)
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
