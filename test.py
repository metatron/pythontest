import numpy as np


D_in, D_out = 2,1

x = np.random.randn(2)
print(x)

y = np.random.randn(1)
print(y)


w1 = np.random.randn(2,2)
b1 = np.random.randn(2)

w2 = np.random.randn(2)
b2 = np.random.randn(1)

learning_rate = 1e-6


def _numerical_gradient_no_batch(f, x):
    h = 1e-4  # 0.0001
    grad = np.zeros_like(x)

    for idx in range(x.size):
        tmp_val = x[idx]
        x[idx] = float(tmp_val) + h
        fxh1 = f(x)  # f(x+h)

        x[idx] = tmp_val - h
        fxh2 = f(x)  # f(x-h)
        grad[idx] = (fxh1 - fxh2) / (2 * h)

        x[idx] = tmp_val  # 値を元に戻す

    return grad


def numerical_gradient(f, X):
    if X.ndim == 1:
        return _numerical_gradient_no_batch(f, X)
    else:
        grad = np.zeros_like(X)

        for idx, x in enumerate(X):
            grad[idx] = _numerical_gradient_no_batch(f, x)

        return grad

def function_2(x):
    if x.ndim == 1:
        return np.sum(x ** 2)
    else:
        return np.sum(x ** 2, axis=1)


#for t in range(500):
h = x.dot(w1)+b1
h_relu = np.maximum(h,0)
y_pred = h_relu.dot(w2)+b2
print(y_pred)

loss = np.square(y_pred - y).sum()
print(loss)



grad_y_pred = 2.0 * (y_pred - y)
grad_w2 = h_relu.T.dot(grad_y_pred)
print(grad_w2)
grad_h_relu = grad_y_pred.dot(w2.T)
grad_h = grad_h_relu.copy()
grad_h[h < 0] = 0
grad_w1 = x.T.dot(grad_h)
print(grad_w1)