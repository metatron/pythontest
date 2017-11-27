import torch
import numpy as np
from torch.autograd import Variable
import stockstats as stss
import pandas as pd

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("3632.csv"))
#print(stock.as_matrix(columns=['high','low','open','volume']))
inVals = np.array(stock.as_matrix(columns=['close','high','low','open','volume']))
closeList = np.array(stock.as_matrix(columns=['close']))

tVals = torch.zeros(len(closeList))
for i in range(len(closeList)-1):
    if(closeList[i+1] > closeList[i] ):
        tVals[i] = 1
    else:
        tVals[i] = 0


rowLen = len(stock.as_matrix(columns=['close']))

#stock info
D_in, H, D_out = 5, 100, 1
# x = torch.from_numpy(inVals)
# y = torch.from_numpy(tVals)
num_directions=1
num_layers=2
batch=1



# model = torch.nn.Sequential(
#     torch.nn.Linear(D_in, H),
#     torch.nn.Sigmoid(),
#     torch.nn.Linear(H, H),
#     torch.nn.Sigmoid(),
#     torch.nn.Linear(H, D_out),
# )

class Sequence(torch.nn.Module):
    def __init__(self):
        super(Sequence, self).__init__()
        self.lstm1 = torch.nn.LSTMCell(D_in, H)
        self.lstm2 = torch.nn.LSTMCell(H, D_out)

    def forward(self, input, future = 0):
        outputs = []
        h_t = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)
        c_t = Variable(torch.zeros(input.size(0), H).float(), requires_grad=False)
        h_t2 = Variable(torch.zeros(input.size(0), D_out).float(), requires_grad=False)
        c_t2 = Variable(torch.zeros(input.size(0), D_out).float(), requires_grad=False)

        for input_t in input:
            h_t, c_t = self.lstm1(input_t, (h_t, c_t))
            h_t2, c_t2 = self.lstm2(h_t, (h_t2, c_t2))
            outputs += [h_t2]
        for i in range(future):# if we should predict the future
            h_t, c_t = self.lstm1(h_t2, (h_t, c_t))
            h_t2, c_t2 = self.lstm2(h_t, (h_t2, c_t2))
            outputs += [h_t2]
        outputs = torch.stack(outputs, 1).squeeze(2)
        return outputs

tmpX = torch.from_numpy(inVals[0])
input = Variable(tmpX, requires_grad=True).float()

model = Sequence()
model.float()

loss_fn = torch.nn.MSELoss(size_average=False)

#Using Adam gradient logic
learning_rate = 1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

canProceed=False

for i in range(len(inVals)):
    while canProceed != True:
        tmpX = torch.from_numpy(inVals[i])
        x = Variable(tmpX, requires_grad=True).float()

        tmpY = torch.zeros(1)
        tmpY[0] = tVals[i]
        y = Variable(tmpY, requires_grad=False).float()

        #通常のモデル
        #y_pred,(ht,ct) = model(x)

        y_pred = model(input)

        loss = loss_fn(y_pred, y)
        if (loss.data[0] <= learning_rate):
            canProceed = True
            print(y, y_pred, loss.data[0])

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

    canProceed = False

print("finished training")

indx=0
testX = Variable(torch.from_numpy(inVals[indx])).float()
print(model(testX), tVals[indx])

#一番最後は
#799,814,791,806,2139200
#これを入力して明日の予測をする
print("Tomorrow prediction")

tomorrowX = Variable(torch.from_numpy(np.array([799,814,791,806,2139200]))).float()
print(model(tomorrowX))