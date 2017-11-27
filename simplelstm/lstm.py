import torch
import numpy as np
from torch.autograd import Variable
import stockstats as stss
import pandas as pd

#stock info
D_in, H, D_out = 5, 100, 1
# x = torch.from_numpy(inVals)
# y = torch.from_numpy(tVals)
num_directions=1
num_layers=2
batch=1

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("../3632.csv"))
print(stock.as_matrix(columns=['high','low','open','volume']))

#macd初期化
stock['macd']
#print(stock.as_matrix(columns=['close','high','low','open','volume','macd']))

inputData = np.array(stock.as_matrix(columns=['high','low','open','volume','macd']))
targetData = np.array(stock.as_matrix(columns=['close']))
#print(target)

class Sequence(torch.nn.Module):
    def __init__(self):
        super(Sequence, self).__init__()
        self.lstm1 = torch.nn.LSTMCell(D_in, H)
        self.lstm2 = torch.nn.LSTMCell(H, H)
        self.linear = torch.nn.Linear(H, D_out)

    def forward(self, input, future = 0):
        outputs = []
        h_t = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)
        c_t = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)
        h_t2 = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)
        c_t2 = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)

        for input_t in input:
            h_t, c_t = self.lstm1(input_t, (h_t, c_t))
            h_t2, c_t2 = self.lstm2(h_t, (h_t2, c_t2))
            output = self.linear(h_t2)
            outputs += [output]

        for i in range(future):# if we should predict the future
            h_t, c_t = self.lstm1(output, (h_t, c_t))
            h_t2, c_t2 = self.lstm2(h_t, (h_t2, c_t2))
            output = self.linear(h_t2)
            outputs += [output]

        outputs = torch.stack(outputs, 1).squeeze(2)
        return outputs



# set random seed to 0
np.random.seed(0)
torch.manual_seed(0)

inVal = Variable(torch.from_numpy(inputData).float(), requires_grad=False)
targetVal = Variable(torch.from_numpy(targetData).float(), requires_grad=False)

# build the model
seq = Sequence()
seq.float()
criterion = torch.nn.MSELoss()
# use LBFGS as optimizer since we can load the whole data to train
optimizer = torch.optim.LBFGS(seq.parameters(), lr=0.8)


# begin to train
for y in range(245):
    print('*************************STEP: ', y)
    input = inVal[y:y+1]
    target = targetVal[y]

    def closure():
        optimizer.zero_grad()
        out = seq(input)
        loss = criterion(out, target)
        print('out:{0}, loss:{1}'.format(out, loss.data.numpy()[0]))
        loss.backward()
        return loss

    optimizer.step(closure)


# print('*******************predict')
# predIn = Variable(torch.from_numpy([[556,545,555,1243300, 0.0]]).float(), requires_grad=False)
# predOut = seq(predIn)