
import numpy as np
import time
n = 800
A = np.random.rand(n, n).astype(np.float64)
B = np.random.rand(n, n).astype(np.float64)
start = time.time()
# Dense matrix operations
C = np.dot(A, B)
D = np.linalg.inv(C + np.eye(n) * 0.1)
E = np.dot(C, D)
result = np.trace(E)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
