import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import RMSprop, SGD

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error


PATH = "seqData.pt"

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))
# print(stock.as_matrix(columns=['high','low','open','volume']))

#macd初期化
stock['macd']
# print(stock.as_matrix(columns=['open','close']))

datasetX = np.array(stock.as_matrix(columns=['open'])[:100], dtype='float')
datasetY = np.array(stock.as_matrix(columns=['close'])[:100], dtype='float')

scaler = MinMaxScaler(feature_range=(0, 1))
trainX = scaler.fit_transform(datasetX)
trainY = scaler.fit_transform(datasetY)

model = Sequential()
model.add(Dense(100, input_shape=(1,)))
model.add(Activation(activation="softmax"))
model.add(Dense(1))

sgd = SGD(lr=0.1)
model.compile(loss='mean_squared_error', optimizer=sgd)

model.fit(trainX, trainY, epochs=100, batch_size=1)

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

plt.plot(trainY)
plt.plot(predictedY[:,0])

plt.show()
