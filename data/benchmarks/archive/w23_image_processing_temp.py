
import numpy as np
import time
from scipy import ndimage

n = 2000
image = np.random.rand(n, n)
kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
start = time.time()
# Convolution
filtered = ndimage.convolve(image, kernel, mode='constant')
# Gaussian blur
blurred = ndimage.gaussian_filter(filtered, sigma=1.0)
# Edge detection
edges = np.abs(np.gradient(blurred))
result = np.sum(edges)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
