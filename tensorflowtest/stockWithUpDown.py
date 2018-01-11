# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/
# https://qiita.com/rakichiki/items/a514f3a4f3e979ace3c9

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

from utils import addColumn, dataByClose, dataUpDown

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

#Rsiデータ取得
allRsi  = np.array(stock.as_matrix(columns=['rsi_6']), dtype ='float')
#[0] = NaN
allRsi[0] = 0

#上がった下がったデータ
allDataUpDown = dataUpDown.data_updown(stock)


# ノーマライズは学習用、テスト用両方一気にやってしまわないといけない気がする。
scaler = MinMaxScaler(feature_range=(0, 1))
allDataNormalizedX = scaler.fit_transform(allDataX)

# 各パラメータは別でノーマライズ
rsiScaler = MinMaxScaler(feature_range=(0, 1))
allRsiNormalized = rsiScaler.fit_transform(allRsi)



TRAINING_MAX_POS = 200
TESTING_MAX_POS = TRAINING_MAX_POS + 46


# 始値を入力値、上がり下がりを学習値としてデータ作成
trainX = allDataNormalizedX[:TRAINING_MAX_POS]
trainY = allDataUpDown[:TRAINING_MAX_POS]

# 各パラメータを追加
trainX = addColumn.add_column(trainX, allRsiNormalized[:TRAINING_MAX_POS])

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

print(trainX)


#予想するデータを用意
testDatasetY = allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS]
testX = allDataNormalizedX[TRAINING_MAX_POS:TESTING_MAX_POS]
testY = allDataUpDown[TRAINING_MAX_POS:TESTING_MAX_POS]

# 各パラメータを追加
testX = addColumn.add_column(testX, allRsiNormalized[TRAINING_MAX_POS:TESTING_MAX_POS])

# reshape input to be [samples, time steps, features]
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

print(testY)

model = Sequential()

my_file = Path('lstm_model.h5')
if my_file.is_file():
    model = load_model('lstm_model.h5')
else:
    # 2つ以上のLSTMレイヤーを組み合わせる場合、一つ前のLSTMレイヤのreturn_sequences=Trueにする。
    model.add(LSTM(20,input_shape=(1,2),return_sequences=True))
    # model.add(Dropout(0.1))
    model.add(LSTM(20))
    # model.add(Dropout(0.1))
    # 最終出力次元
    model.add(Dense(3, activation='sigmoid'))

    # sgd = SGD(lr=0.1)
    # model.compile(loss='mean_squared_error', optimizer=sgd)

    rmsprop = RMSprop()
    model.compile(loss='categorical_crossentropy', optimizer=rmsprop, metrics=['accuracy'])

    model.fit(trainX, trainY, epochs=50, batch_size=2)

    # save keras model
    # model.save('lstm_model.h5')

# make predictions
#trainPredict = model.predict(trainX)
trainPredict = model.predict(testX)

# predictedY = scaler.inverse_transform(trainPredict)
print(trainPredict)
exit()

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
