import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

DATA_NUM=100
X_LEN = 2

# Sinデータ用意
x = []
for i in range(0,DATA_NUM):
    val = i/10.0
    x.append(val)

y=np.sin(x)

inData = np.zeros((DATA_NUM,X_LEN), dtype=float)
index=0
for data in x:
    inData[index]=[data,y[index]]
    index += 1

print(inData)

#Pytorchクラス



plt.figure(figsize=(20, 5))
plt.title('Predict future values for time sequences', fontsize=10)
plt.xlabel('x', fontsize=10)
plt.ylabel('y', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

plt.plot(x,y)

plt.show()



