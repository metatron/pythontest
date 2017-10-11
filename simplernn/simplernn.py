import torch
from torch.autograd import Variable

#https://stackoverflow.com/questions/45022734/understanding-a-simple-lstm-pytorch

#input_size, hidden_size, num_layers
rnn = torch.nn.RNN(5, 10, 2)
#seq_len, batch, input_size
input = Variable(torch.randn(5,1))
#num_layers, batch, hidden_size
h0 = Variable(torch.randn(5+10,2))
output, hn = rnn(input, h0)
