# https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/
# https://keras.io/ja/layers/recurrent/

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM
from keras.optimizers import RMSprop, SGD

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error


PATH = "seqData.pt"

# convert an array of values into a dataset matrix
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
        b = [dataset[i + look_back, 0]]
        dataY.append(b)
    return np.array(dataX), np.array(dataY)

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))
# print(stock.as_matrix(columns=['high','low','open','volume']))

#macd初期化
stock['macd']
# print(stock.as_matrix(columns=['open','close']))

# 始値を入力値、終値を学習値としてデータ作成
datasetX = np.array(stock.as_matrix(columns=['open', 'macd'])[:100], dtype='float')
datasetY = np.array(stock.as_matrix(columns=['close'])[:100], dtype='float')

# t+1 = tに加工したデータを作成
# datasetArray = stock.as_matrix(columns=['close'])[:100]
# datasetArray = datasetArray.reshape(100,1)
# datasetX,datasetY = create_dataset(datasetArray.astype('float32'))

scaler = MinMaxScaler(feature_range=(0, 1))
trainX = scaler.fit_transform(datasetX)
trainY = scaler.fit_transform(datasetY)

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
#testX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

model = Sequential()
# model.add(Dense(100, input_shape=(1,)))
# model.add(Activation(activation="softmax"))
model.add(LSTM(4,input_shape=(1,2)))

model.add(Dense(1))

# sgd = SGD(lr=0.1)
model.compile(loss='mean_squared_error', optimizer='adam')

model.fit(trainX, trainY, epochs=50, batch_size=1)

# make predictions
trainPredict = model.predict(trainX)
predictedY = scaler.inverse_transform(trainPredict)
print(predictedY)

#plot graph
plt.figure(figsize=(20, 5))
plt.title('Predict future values for time sequences', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.ylabel('y', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

plt.plot(datasetY)
plt.plot(predictedY)# [:,0])

plt.show()
