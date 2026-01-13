
import numpy as np
import time

# Simple neural network forward pass
n_input = 256
n_hidden = 512
n_output = 128
batch_size = 100

W1 = np.random.rand(n_input, n_hidden).astype(np.float32)
W2 = np.random.rand(n_hidden, n_output).astype(np.float32)
X = np.random.rand(batch_size, n_input).astype(np.float32)

start = time.time()
# Forward pass
Z1 = np.dot(X, W1)
A1 = np.maximum(0, Z1)  # ReLU
Z2 = np.dot(A1, W2)
A2 = 1 / (1 + np.exp(-Z2))  # Sigmoid
result = np.sum(A2)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
