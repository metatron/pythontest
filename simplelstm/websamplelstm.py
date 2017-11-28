import numpy as np
import torch
import random
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.autograd as autograd
from torch.autograd import Variable
import torchvision.transforms as T

class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.fc1 = nn.Linear(5,5)
        self.lstm = nn.LSTMCell(5, 2)
        self.fc2 = nn.Linear(2,1)

    def forward(self, x, hidden):
        y = self.fc1(x)
        hx,cx = self.lstm(y,hidden)
        y = self.fc2(hx)

        return y, hx,cx


model = Policy()
optimizer = optim.Adam(model.parameters())

step = 1

for i in range(100):
    yhat = Variable(torch.zeros(step,1))
    target = Variable(torch.zeros(step,1))
    target[-1,0] = 1
    cx = Variable(torch.zeros(1,2))
    hx = Variable(torch.zeros(1,2))
    hidden= [hx,cx]

    for j in range(step):
        x = Variable(torch.zeros(1,5))
        if j is 0:
            x += 1
            x = Variable(x.data)
        y, hx,cx = model(x,hidden)
        # print (hx.data.numpy())
        hidden = (hx,cx)
        print ('y',y)
        print ('hidden',hidden)
        yhat[j] = y[0]

    print ('done - the last output should be one')
    #learning
    optimizer.zero_grad()
    error = (yhat-target).pow(2).mean()
    print (error)
    error.backward()
    optimizer.step()