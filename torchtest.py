import torch
import numpy as np
from torch.autograd import Variable

# N, D_in, H, D_out = 4, 2, 4, 1
#
# x = Variable(torch.randn(N,D_in))
# y = Variable(torch.randn(N, D_out), requires_grad=False)

D_in, H, D_out = 2, 100, 1

x = torch.from_numpy(np.array([[0, 0], [1, 0], [0, 1], [1, 1]]))
y = torch.from_numpy(np.array([[0], [1], [1], [0]]))
x = Variable(x.float())
x.requires_grad = True
y = Variable(y.float())
y.requires_grad = False

# Use the nn package to define our model as a sequence of layers. nn.Sequential
# is a Module which contains other Modules, and applies them in sequence to
# produce its output. Each Linear Module computes output from input using a
# linear function, and holds internal Variables for its weight and bias.
model = torch.nn.Sequential(
    torch.nn.Linear(D_in, H),
    torch.nn.ReLU(),
    torch.nn.Linear(H, D_out),
)

loss_fn = torch.nn.MSELoss(size_average=False)

learning_rate = 1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

for t in range(10000):
    y_pred = model(x)

    # Compute and print loss. We pass Variables containing the predicted and true
    # values of y, and the loss function returns a Variable containing the
    # loss.
    loss = loss_fn(y_pred, y)
    if(t%1000 == 0):
        print(t, loss.data[0])

    # Zero the gradients before running the backward pass.
    #model.zero_grad()
    optimizer.zero_grad()

    loss.backward()

    # Update the weights using gradient descent. Each parameter is a Variable, so
    # we can access its data and gradients like we did before.
    #for param in model.parameters():
    #    param.data -= learning_rate * param.grad.data
    optimizer.step()

print("finished training")
print(model(x[0]))
print(model(x[1]))
print(model(x[2]))
print(model(x[3]))
