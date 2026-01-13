
import random
import time
n = 10000000
start = time.time()
inside = 0
for _ in range(n):
    x = random.random()
    y = random.random()
    if x*x + y*y <= 1.0:
        inside += 1
pi_estimate = 4.0 * inside / n
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
