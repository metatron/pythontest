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


class LstmModel(torch.nn.Module):
    def __init__(self):
        super(LstmModel, self).__init__()
        self.lstm1 = torch.nn.LSTMCell(input_size, hidden_size)
        self.lstm1 = torch.nn.LSTMCell(hidden_size, output_size)

    def forward(self, input):
        outputs = []
        h_t = Variable(torch.zeros(input.size(0), hidden_size).float(), requires_grad=False)
        c_t = Variable(torch.zeros(input.size(0), hidden_size).float(), requires_grad=False)
        h_t2 = Variable(torch.zeros(input.size(0), output_size).float(), requires_grad=False)
        c_t2 = Variable(torch.zeros(input.size(0), output_size).float(), requires_grad=False)

        for input_t in input:
            h_t, c_t = self.lstm1(input_t, (h_t, c_t))
            h_t2, c_t2 = self.lstm2(h_t, (h_t2, c_t2))
            outputs += [h_t2]
#        outputs = torch.stack(outputs, 1).squeeze(2)
        return outputs

rnn = LstmModel()
rnn.float()

#(seq_len, batch, input_size)
input = Variable(torch.randn(batch, input_size))

target = Variable(torch.randn(input_size))

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
        output = rnn(input)
        exit()

        # Step 4. Compute the loss, gradients, and update the parameters by
        #  calling optimizer.step()
        loss = loss_function(output, target)

        if(epoch%100 == 0):
            print("epoch: {0}, loss: {1}". format(epoch, loss))
            print(output, target)

        loss.backward(retain_graph=True)
        optimizer.step()
