import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers import LSTM, Embedding, Conv1D, Flatten, MaxPooling1D
from keras.optimizers import RMSprop, SGD, Adam
from keras.models import load_model
from keras.callbacks import EarlyStopping
from pathlib import Path
import tensorflow as tf


class StockPatternDetect():
    def __init__(self, trainX, trainY, testX, testY, saveModel=True):
        self.trainX = trainX
        self.trainY = trainY
        self.testX = testX
        self.testY = testY
        self.saveModel = saveModel


    def train_model(self, epochs_=50, modelfilepath='cnn_model.h5'):
        model = Sequential()

        my_file = Path(modelfilepath)
        if my_file.is_file():
            model = load_model(modelfilepath)
        else:
            # filter: 出力、kernel_size: 各filterの長さ
            model.add(Conv1D(filters=40, kernel_size=self.trainX.shape[1], padding='same', input_shape=(1, self.trainX.shape[2])))
            # model.add(LSTM(20, return_sequences=True, activation='relu'))
            model.add(MaxPooling1D(pool_size=2, padding="same"))
            model.add(Dense(20, activation='tanh'))
            model.add(Dropout(0.2))
            model.add(Flatten())
            model.add(Dropout(0.2))
            # 最終出力次元
            model.add(Dense(1, activation='tanh'))

            # sgd = SGD(lr=0.1)
            # model.compile(loss='mean_squared_error', optimizer=sgd)

            model.summary()

            model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

            # earlyStp = EarlyStopping(mode='auto', patience=5) #->やらない方が正確
            # validation_split (訓練データの一部をバリデーションデータセットとして使用）
            model.fit(self.trainX, self.trainY, epochs=epochs_, batch_size=1)#, callbacks=[earlyStp], validation_split=0.3)

            # save keras model
            if(self.saveModel):
                model.save(modelfilepath)

        # make predictions
        self.trainPredict = model.predict(self.testX)

        return self.trainPredict
