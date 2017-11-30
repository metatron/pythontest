import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim
import numpy as np
import matplotlib
import matplotlib.pyplot as plt



x = []
for i in range(0,100):
    val = i/10.0
    x.append(val)

print(x)

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



