import torch
import torch.optim as optim
from torch.autograd import Variable

#https://stackoverflow.com/questions/45022734/understanding-a-simple-lstm-pytorch

#input_size, hidden_size, num_layers
input_size=5
hidden_size=10
num_layers=2
batch=1
seq_len=1

rnn = torch.nn.RNN(input_size, hidden_size, num_layers)
#seq_len, batch, input_size
input = Variable(torch.randn(seq_len,batch,input_size), requires_grad=False)
target = Variable(torch.randn(seq_len,batch,input_size), requires_grad=False)
#num_layers, batch, hidden_size
h0 = Variable(torch.randn(num_layers,batch,hidden_size), requires_grad=False)
output, hn = rnn(input, h0)

criterion = torch.nn.NLLLoss()
optimizer = optim.LBFGS(rnn.parameters(), lr=0.8)

learning_rate = 0.00001



for i in range(15):
    optimizer.zero_grad()
    output,hn = rnn(input,hn)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
