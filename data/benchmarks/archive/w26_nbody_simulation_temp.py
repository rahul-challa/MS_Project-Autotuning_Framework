
import numpy as np
import time

n = 1000
positions = np.random.rand(n, 3) * 100
velocities = np.random.rand(n, 3) * 0.1
masses = np.random.rand(n) * 10

start = time.time()
for step in range(10):
    forces = np.zeros((n, 3))
    for i in range(n):
        for j in range(n):
            if i != j:
                diff = positions[j] - positions[i]
                dist = np.linalg.norm(diff)
                if dist > 0.1:
                    force = masses[i] * masses[j] / (dist ** 2)
                    forces[i] += force * diff / dist
    velocities += forces * 0.01
    positions += velocities * 0.01
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
