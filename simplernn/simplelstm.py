import torch
from torch.autograd import Variable
import torch.optim as optim

torch.manual_seed(1)


#https://stackoverflow.com/questions/45022734/understanding-a-simple-lstm-pytorch
#http://pytorch.org/docs/master/nn.html

num_layers=2
num_directions = 1 #by default, 1
seq_len = 1 #the number of time steps in each input stream.
input_size=4
batch = 1
hidden_size = 4

output_size = 1


rnn = torch.nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers) #(10, 20, 2)


#(seq_len, batch, input_size)
input = Variable(torch.randn(seq_len, batch, input_size))

target = Variable(torch.randn(input_size))

#(num_layers * num_directions, batch, hidden_size)
h0 = Variable(torch.randn(num_layers*num_directions, batch, hidden_size))

#num_layers * num_directions, batch, hidden_size
c0 = Variable(torch.randn(num_layers*num_directions, batch, hidden_size))

output, (hn, cn) = rnn(input, (h0, c0))

print(input)
print(target)

loss_function = torch.nn.MSELoss()
optimizer = optim.Adamax(rnn.parameters(), lr=0.8)


for epoch in range(1000):  # again, normally you would NOT do 300 epochs, it is toy data
    for t in range(batch):
        # Step 1. Remember that Pytorch accumulates gradients.
        # We need to clear them out before each instance
        rnn.zero_grad()

        # Step 2. Run our forward pass.
        output, (hn, cn) = rnn(input, (hn, cn))


        # Step 4. Compute the loss, gradients, and update the parameters by
        #  calling optimizer.step()
        loss = loss_function(output, target)

        if(epoch%100 == 0):
            print("epoch: {0}, loss: {1}". format(epoch, loss))
            print(output, target)

        loss.backward(retain_graph=True)
        optimizer.step()
