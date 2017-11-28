import torch
import numpy as np
from torch.autograd import Variable
import stockstats as stss
import pandas as pd
import os

import matplotlib
import matplotlib.pyplot as plt



#stock info
D_in, H, D_out = 5, 50, 1
# x = torch.from_numpy(inVals)
# y = torch.from_numpy(tVals)
num_directions=1
num_layers=2
batch=1

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


class Sequence(torch.nn.Module):
    def __init__(self):
        super(Sequence, self).__init__()
        self.linear1 = torch.nn.Linear(D_in, H)
        self.lstm1 = torch.nn.LSTMCell(H, H)
        self.linear2 = torch.nn.Linear(H, D_out)

    def forward(self, input, hidden):
        y = self.linear1(input)
        h_t,c_t = self.lstm1(y, hidden)
        output = self.linear2(h_t)

        return output, h_t,c_t


# set random seed to 0
np.random.seed(0)
torch.manual_seed(0)

inVal = Variable(torch.from_numpy(inputData).float(), requires_grad=False)
targetVal = Variable(torch.from_numpy(targetData).float(), requires_grad=False)

# build the model
seq = Sequence()

if os.path.isfile(PATH):
    seq.load_state_dict(torch.load(PATH))
else:
    seq.float()
    criterion = torch.nn.MSELoss()
    # use LBFGS as optimizer since we can load the whole data to train
    #optimizer = torch.optim.LBFGS(seq.parameters(), lr=0.8)
    optimizer = torch.optim.Adam(seq.parameters(), lr=1.0)

    cx = Variable(torch.zeros(1,H))
    hx = Variable(torch.zeros(1,H))
    hidden = [hx,cx]

    # begin to train
    for y in range(6):
        input = inVal[y:y+1]
        target = targetVal[y]
        lossF = 1.0
        index=0
        print('********************************STEP: ', y, ' target: ', target)

        while lossF > 0.0001:
            optimizer.zero_grad()
            hidden=(hx,cx)
            out, hx,cx = seq(input, hidden)
            loss = criterion(out, target)
            lossF = loss.data.numpy()[0]
            if index%10 == 0:
                print('out:{0}, loss:{1}'.format(out, lossF))
            loss.backward(retain_graph=True)
            optimizer.step()
            index+=1

    print('********************************Saving Model')

    torch.save(seq.state_dict(), PATH)


print('*******************predict')


input = inVal[0:1]
print(input)
out = seq(input)
print(out)

pred=[]
for y in range(245):
    input = inVal[y:y + 1]
    out = seq(input)
    pred.append(out.data.numpy()[0,0])


plt.figure(figsize=(30, 10))
plt.title('Predict future values for time sequences', fontsize=20)
plt.xlabel('x', fontsize=20)
plt.ylabel('y', fontsize=20)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.plot(targetData, label="real")
plt.plot(pred, label="pred")

plt.show()

