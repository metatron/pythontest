# https://qiita.com/hiroeorz@github/items/33b85529be0829f34973
# https://kuune.org/text/

import keras
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM, Embedding, Convolution2D
from keras.optimizers import RMSprop, SGD
from keras.models import load_model
from pathlib import Path
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

import utils.dataUpDown as dataUpDown
from sklearn.preprocessing import MinMaxScaler

from keras.layers.advanced_activations import LeakyReLU, ELU



dataX = np.array([[680, 670], [674, 675], [678, 680], [690, 685], [680, 675], [670, 671]])
dataY = np.array([[0], [1], [1], [0], [0], [1]])

scaler = MinMaxScaler(feature_range=(0,1))
dataX = scaler.fit_transform(dataX)


TEST_POS = 10
trainX = dataX[:TEST_POS]
trainY = dataY[:TEST_POS]



# trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
# trainY = np.reshape(trainY, (trainY.shape[0], 1, trainY.shape[1]))



leaky_relu = LeakyReLU()

model = Sequential()
model.add(Convolution2D())
model.add(Dense(10, name='dense_1'))
# 2つ以上のLSTMレイヤーを組み合わせる場合、一つ前のLSTMレイヤのreturn_sequences=Trueにする。
# model.add(LSTM(10))
# 最終出力次元
model.add(Dense(1, activation='relu', name='dense_2'))

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(trainX, trainY, epochs=50, batch_size=1)



#test
# testX = [dataX[10]]
# textY = [dataY[10]]
# testX = np.reshape(testX, (1,1,1))

result = model.predict(trainX)

print(result, trainY)