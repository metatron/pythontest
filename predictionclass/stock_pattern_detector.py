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


class StockPatternDetect():
    def __init__(self, trainX, trainY, testX, testY):
        self.trainX = trainX
        self.trainY = trainY
        self.testX = testX
        self.testY = testY


    def train_model(self, epochs_=50, modelfilepath='cnn_model.h5'):
        model = Sequential()

        my_file = Path(modelfilepath)
        if my_file.is_file():
            model = load_model(modelfilepath)
        else:
            # filter: 出力、kernel_size: 各filterの長さ
            model.add(Conv1D(filters=40, kernel_size=self.trainX.shape[1], padding='same', input_shape=(1, self.trainX.shape[2])))
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

            model.fit(self.trainX, self.trainY, epochs=epochs_, batch_size=1)

            # save keras model
            model.save(modelfilepath)

        # make predictions
        self.trainPredict = model.predict(self.testX)

        return self.trainPredict
