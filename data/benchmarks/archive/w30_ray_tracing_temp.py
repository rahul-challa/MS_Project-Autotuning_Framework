
import numpy as np
import time

def ray_sphere_intersect(ray_origin, ray_dir, sphere_center, sphere_radius):
    oc = ray_origin - sphere_center
    a = np.dot(ray_dir, ray_dir)
    b = 2.0 * np.dot(oc, ray_dir)
    c = np.dot(oc, oc) - sphere_radius * sphere_radius
    discriminant = b * b - 4 * a * c
    return discriminant > 0

n_rays = 100000
n_spheres = 1000
ray_origins = np.random.rand(n_rays, 3)
ray_dirs = np.random.rand(n_rays, 3)
ray_dirs = ray_dirs / np.linalg.norm(ray_dirs, axis=1, keepdims=True)
spheres = np.random.rand(n_spheres, 3) * 10
radii = np.random.rand(n_spheres) * 2

start = time.time()
hits = 0
for i in range(n_rays):
    for j in range(n_spheres):
        if ray_sphere_intersect(ray_origins[i], ray_dirs[i], spheres[j], radii[j]):
            hits += 1
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
