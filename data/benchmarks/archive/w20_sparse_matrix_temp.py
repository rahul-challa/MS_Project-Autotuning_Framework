
import numpy as np
import scipy.sparse
import time
n = 2000
density = 0.01
A = scipy.sparse.random(n, n, density=density, format='csr')
x = np.random.rand(n)
start = time.time()
y = A.dot(x)
z = A.T.dot(y)
result = np.sum(z)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
