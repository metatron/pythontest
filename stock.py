import torch
import numpy as np
from torch.autograd import Variable
import stockstats as stss
import pandas as pd

#保存されたCSVを読み込んでstockstatsフォーマットにする
stock = stss.StockDataFrame().retype(pd.read_csv("7203.csv"))
#print(stock.as_matrix(columns=['high','low','open','volume']))
inVals = np.array(stock.as_matrix(columns=['high','low','open','volume']))
tVals = np.array(stock.as_matrix(columns=['close']))

rowLen = len(stock.as_matrix(columns=['close']))
#stock info
D_in, H, D_out = 4, 1000, 1
x = torch.from_numpy(inVals)
y = torch.from_numpy(tVals)

#XOR test
# D_in, H, D_out = 2, 100, 1
# x = torch.from_numpy(np.array([[0, 0], [1, 0], [0, 1], [1, 1]]))
# y = torch.from_numpy(np.array([[0], [1], [1], [0]]))


x = Variable(x.float())
x.requires_grad = True
y = Variable(y.float())
y.requires_grad = False


model = torch.nn.Sequential(
    torch.nn.Linear(D_in, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, D_out),
)

loss_fn = torch.nn.MSELoss(size_average=False)

#Using Adam gradient logic
learning_rate = 1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

for t in range(100000):
    y_pred = model(x)

    loss = loss_fn(y_pred, y)
    if(t%1000 == 0):
        print(t, loss.data[0])

    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

print("finished training")
print(model(x[0]))
print(model(x[1]))
print(model(x[2]))
print(model(x[3]))
