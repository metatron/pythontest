# Stock Prediction: http://www.jakob-aungiers.com/articles/a/LSTM-Neural-Network-for-Time-Series-Prediction
# http://caffe.classcat.com/2017/04/15/pytorch-tutorial-cifar10/
# https://qiita.com/perrying/items/857df46bb6cdc3047bd8

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F

import torch.optim as optim
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import stockstats as stss
import pandas as pd


#Pytorchクラス
input_size=5
hidden_size=100
output_size=1
num_layers=2


PATH = "seqData.pt"

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))
# print(stock.as_matrix(columns=['high','low','open','volume']))

#macd初期化
stock['macd']
print(stock.as_matrix(columns=['high','low','open','volume','macd']))

inputData = np.array(stock.as_matrix(columns=['high','low','open','volume','macd']))
targetData = np.array(stock.as_matrix(columns=['close']))
#print(target)


class MyLSTM(nn.Module):
    def __init__(self):
        super(MyLSTM, self).__init__()
        self.fc1 = nn.Linear(input_size,hidden_size)
        self.lstm = nn.LSTMCell(hidden_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size,output_size)


    def forward(self, x):
        hx = Variable(torch.zeros(output_size, hidden_size))
        cx = Variable(torch.zeros(output_size, hidden_size))
        hidden = [hx, cx]

        y = self.fc1(x)
        hx,cx = self.lstm(y,hidden)
        y = self.fc2(hx)

        return y, hx,cx

rnn = MyLSTM()


inputVal = Variable(torch.from_numpy(inputData).float(), requires_grad=False)
targetVal = Variable(torch.from_numpy(targetData).float(), requires_grad=False)

# トレーニング
criterion = nn.MSELoss()
optimizer = optim.RMSprop(rnn.parameters(), lr=0.8)


hidden=()
for i in range(50):
    print('STEP: ', i)
    optimizer.zero_grad()
    hx = Variable(torch.zeros(output_size, hidden_size))
    cx = Variable(torch.zeros(output_size, hidden_size))
    hidden = [hx, cx]

    def closure():
        optimizer.zero_grad()
        out, hx,cx = rnn(inputVal)
        loss = criterion(out, targetVal)
        if(i%10 == 0):
            print('loss:', loss.data.numpy()[0])
        loss.backward()
        return loss

    optimizer.step(closure)

# y2 = output.data.numpy()

# Prediction
print('**************** PREDICTION ****************')

pred, hr, cr = rnn(inputVal)
loss = criterion(pred, targetVal)
print('test loss:', loss.data.numpy()[0])
y2 = pred.data.numpy()
#print(pred)

# exit(1)

plt.figure(figsize=(20, 5))
plt.title('Predict future values for time sequences', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.ylabel('y', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

plt.plot(targetData)
plt.plot(y2)

plt.show()



