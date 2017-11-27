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
#print(stock.as_matrix(columns=['high','low','open','volume']))

#macd初期化
stock['macd']
#print(stock.as_matrix(columns=['close','high','low','open','volume','macd']))

inVals = np.array(stock.as_matrix(columns=['high','low','open','volume','macd']))
target = np.array(stock.as_matrix(columns=['close']))
#print(target)

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
