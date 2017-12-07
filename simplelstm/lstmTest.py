import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

DATA_NUM=100
X_LEN = 2

# Sinデータ用意
x = []
for i in range(0,DATA_NUM):
    val = i/10.0
    x.append(val)

# sinグラフ予測
y=np.sin(x)

# 2x+1グラフ予測
#y=2*np.array(x)+1

inData = np.zeros((DATA_NUM,X_LEN), dtype=float)

index=0
for data in x:
    inData[index]=[data,y[index]]
    index += 1

#1カラム目（sinグラフでのx値）を選出(y:100個、x:1個のマトリックスに修正）
input=np.reshape(inData[:,0],(100,1))

#2カラム目（y値）を選出
target=inData[:,1]


#Pytorchクラス
input_size=1
hidden_size=20
output_size=1
num_layers=2


class MyLSTM(nn.Module):
    def __init__(self):
        super(MyLSTM, self).__init__()
        self.fc1 = nn.Linear(input_size,hidden_size)
        self.lstm = nn.LSTMCell(hidden_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size,output_size)

    def forward(self, x, hidden):
        y = self.fc1(x)
        hx,cx = self.lstm(y,hidden)
        y = self.fc2(hx)

        return y, hx,cx


rnn = MyLSTM()

# h0 = Variable(torch.randn(output_size, hidden_size))
# c0 = Variable(torch.randn(output_size, hidden_size))
# hidden = [h0,c0]
inputVal = Variable(torch.FloatTensor(input))
targetVal = Variable(torch.FloatTensor(target))
# output,hn,cn = rnn(inputVal, hidden)

# トレーニング
criterion = nn.MSELoss()
optimizer = optim.LBFGS(rnn.parameters(), lr=0.5)

hidden=()
for i in range(10):
    print('STEP: ', i)
    hx = Variable(torch.zeros(output_size, hidden_size))
    cx = Variable(torch.zeros(output_size, hidden_size))
    hidden = [hx, cx]

    def closure():
        optimizer.zero_grad()
        out, hx,cx = rnn(inputVal, hidden)
        loss = criterion(out, targetVal)
        print('loss:', loss.data.numpy()[0])
        loss.backward()
        return loss

    optimizer.step(closure)

# y2 = output.data.numpy()

# Prediction
print('**************** PREDICTION ****************')

pred, hr, cr = rnn(inputVal, hidden)
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

y=y+1
plt.plot(x,y)
plt.plot(x,y2)

plt.show()



