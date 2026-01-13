
import numpy as np
import time
n = 1024
data = np.random.rand(n, n) + 1j * np.random.rand(n, n)
start = time.time()
result = np.fft.fft2(data)
result = np.fft.ifft2(result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
