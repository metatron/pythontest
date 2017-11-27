import torch
import numpy as np
from torch.autograd import Variable
import stockstats as stss
import pandas as pd

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("7203.csv"))
#print(stock.as_matrix(columns=['high','low','open','volume']))
inVals = np.array(stock.as_matrix(columns=['high','low','open','volume']))
closeList = np.array(stock.as_matrix(columns=['close']))

tVals = torch.zeros(len(closeList))
for i in range(len(closeList)-1):
    if(closeList[i+1] > closeList[i] ):
        tVals[i] = 1
    else:
        tVals[i] = 0


rowLen = len(stock.as_matrix(columns=['close']))

#stock info
D_in, H, D_out = 4, 100, 1
# x = torch.from_numpy(inVals)
# y = torch.from_numpy(tVals)


model = torch.nn.Sequential(
    torch.nn.Linear(D_in, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, D_out),
)

loss_fn = torch.nn.MSELoss(size_average=False)

#Using Adam gradient logic
learning_rate = 0.001 #1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

canProceed=False

for i in range(len(inVals)):
    while canProceed != True:
        tmpX = torch.from_numpy(inVals[i])
        x = Variable(tmpX, requires_grad=True).float()

        tmpY = torch.zeros(1)
        tmpY[0] = tVals[i]
        y = Variable(tmpY, requires_grad=False).float()

        y_pred = model(x)

        loss = loss_fn(y_pred, y)
        if (loss.data[0] <= learning_rate):
            canProceed = True
            print(x, y, loss.data[0])

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

    canProceed = False

print("finished training")

indx=0
testX = Variable(torch.from_numpy(inVals[indx])).float()
print(model(testX), tVals[indx])

#一番最後は
#6946,6858,6924,7158400
#これを入力して明日の予測をする
print("Tomorrow prediction")

tomorrowX = Variable(torch.from_numpy(np.array([6946,6858,6924,7158400]))).float()
print(model(tomorrowX))