
import numpy as np
import time

n_particles = 10000
n_steps = 50

particles = np.random.rand(n_particles, 2)
weights = np.ones(n_particles) / n_particles

start = time.time()
for step in range(n_steps):
    # Predict
    particles += np.random.randn(n_particles, 2) * 0.1
    # Update weights (simplified)
    weights *= np.exp(-0.5 * np.sum(particles**2, axis=1))
    weights /= np.sum(weights)
    # Resample
    indices = np.random.choice(n_particles, size=n_particles, p=weights)
    particles = particles[indices]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
