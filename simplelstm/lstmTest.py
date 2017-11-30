import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def drange(begin, end, step):
    n = begin
    while n+step < end:
     yield n
     n += step


print(drange(0.0,1.0,0.1))
x = np.array()
# print(x)

y=np.sin(x)
# print(y)

plt.figure(figsize=(20, 10))
plt.title('Predict future values for time sequences', fontsize=20)
plt.xlabel('x', fontsize=20)
plt.ylabel('y', fontsize=20)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.plot(x,y)

plt.show()



