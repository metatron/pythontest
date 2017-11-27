# -*- coding: utf-8 -*-
import torch
from torch.autograd import Variable
import sys, os
sys.path.append(os.pardir)  # 親ディレクトリのファイルをインポートするための設定
import numpy as np
from dataset.mnist import load_mnist
from PIL import Image

def get_data():
    (x_train, t_train), (x_test, t_test) = load_mnist(flatten=True, normalize=True, one_hot_label=True)
    return x_test, t_test


# N is batch size; D_in is input dimension;
# H is hidden dimension; D_out is output dimension.
N, D_in, H, D_out = 1, 784, 50, 10

# Create random Tensors to hold inputs and outputs, and wrap them in Variables.
# x = Variable(torch.randn(N, D_in))
# y = Variable(torch.randn(N, D_out), requires_grad=False)


class TwoLayerNet(torch.nn.Module):
    def __init__(self, D_in, H, D_out):
        """
        In the constructor we instantiate two nn.Linear modules and assign them as
        member variables.
        """
        super(TwoLayerNet, self).__init__()
        self.linear1 = torch.nn.Linear(D_in, H)
        self.linear2 = torch.nn.Linear(H, D_out)

    def forward(self, x):
        """
        In the forward function we accept a Variable of input data and we must return
        a Variable of output data. We can use Modules defined in the constructor as
        well as arbitrary operators on Variables.
        """
        h_relu = self.linear1(x).clamp(min=0)
        y_pred = self.linear2(h_relu)
        return y_pred


# Use the nn package to define our model and loss function.
model = torch.nn.Sequential(
    torch.nn.Linear(D_in, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, D_out),
)

#model = TwoLayerNet(D_in, H, D_out)


loss_fn = torch.nn.MSELoss(size_average=False)

# Use the optim package to define an Optimizer that will update the weights of
# the model for us. Here we will use Adam; the optim package contains many other
# optimization algoriths. The first argument to the Adam constructor tells the
# optimizer which Variables it should update.
learning_rate = 0.0001 #1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

canProceed = False

result = np.zeros(10, dtype=float)

x,t = get_data()
# for i in range(len(x)):
for i in range(200):
    while canProceed != True:
        # Forward pass: compute predicted y by passing x to the model.
        tmpX = x[i]
        x_v = Variable(torch.from_numpy(x[i]))
        y_pred = model(x_v)
        y_pred.float()

        tmpT  = t[i]
        y_v = Variable(torch.from_numpy(t[i]), requires_grad=False)
        y_v = y_v.float()

        # Compute and print loss.
        loss = loss_fn(y_pred, y_v)
        # print(t[i], loss.data[0])

        if(loss.data[0] <= learning_rate):
            canProceed = True
            print(t[i], loss.data[0])

            #全部埋まったら抜ける
#            result[t[i].argmax()] = loss.data[0]

        # Before the backward pass, use the optimizer object to zero all of the
        # gradients for the variables it will update (which are the learnable weights
        # of the model)
        optimizer.zero_grad()

        # Backward pass: compute gradient of the loss with respect to model
        # parameters
        loss.backward()

        # Calling the step function on an Optimizer makes an update to its
        # parameters
        optimizer.step()

    canProceed = False

rndIndxList = torch.rand(10)*40
rndIndxList = rndIndxList.int()

for indx in rndIndxList:
    testX = Variable(torch.from_numpy(x[indx]))
    textT = t[indx]
    y_pred = model(testX)

    print(textT, y_pred.view(1,10))
