#!/usr/bin/env python3
"""
Workload Registry

Comprehensive registry of all workloads that can be profiled with VTune.
These workloads stress different CPU components and characteristics.
"""

# VTune Collection Types - All Available Types
VTUNE_COLLECTION_TYPES = [
    'hotspots',                    # Basic CPU hotspots
    'microarchitecture-exploration',  # Microarchitecture analysis (requires admin)
    'memory-access',               # Memory access patterns
    'threading',                   # Threading analysis
    'uarch-exploration',           # Alternative microarchitecture exploration
    'bandwidth',                   # Memory bandwidth analysis
    'memory-consumption',          # Memory usage analysis
    'hpc-performance',              # HPC-specific analysis
    # Note: Some types like 'gpu-offload' and 'io' require specific hardware/conditions
]

# Collection types that can be used together (non-conflicting)
COMPATIBLE_COLLECTION_TYPES = {
    'hotspots': ['memory-access', 'threading', 'bandwidth'],
    'microarchitecture-exploration': ['memory-access'],
    'memory-access': ['hotspots', 'bandwidth'],
    'threading': ['hotspots'],
    'uarch-exploration': ['memory-access'],
    'bandwidth': ['memory-access', 'hotspots'],
    'memory-consumption': ['hotspots'],
}

# Comprehensive Workload Definitions
WORKLOADS = {
    # Basic Computational Workloads
    'w1_matrix_mult': {
        'name': 'Matrix Multiplication',
        'description': 'Dense matrix multiplication - tests FPU and memory bandwidth',
        'code': '''
import numpy as np
import time
n = 500
A = np.random.rand(n, n)
B = np.random.rand(n, n)
start = time.time()
C = np.dot(A, B)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'memory-access', 'microarchitecture-exploration', 'bandwidth']
    },
    
    'w2_bubble_sort': {
        'name': 'Bubble Sort',
        'description': 'Sorting algorithm - tests branch prediction and cache',
        'code': '''
import random
import time
n = 10000
arr = [random.randint(1, 1000) for _ in range(n)]
start = time.time()
for i in range(n):
    for j in range(0, n - i - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w3_fft_calc': {
        'name': 'FFT Computation',
        'description': 'Fast Fourier Transform - tests complex math and memory patterns',
        'code': '''
import numpy as np
import time
n = 1000000
data = np.random.rand(n) + 1j * np.random.rand(n)
start = time.time()
result = np.fft.fft(data)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'memory-access', 'microarchitecture-exploration', 'bandwidth']
    },
    
    # Memory-Intensive Workloads
    'w4_memory_intensive': {
        'name': 'Memory Intensive (Poor Locality)',
        'description': 'Strided memory access - tests cache miss handling',
        'code': '''
import numpy as np
import time
n = 2000
arr = np.random.rand(n, n)
start = time.time()
result = 0
for i in range(0, n, 8):
    for j in range(0, n, 8):
        result += arr[i, j]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'bandwidth']
    },
    
    'w5_compute_intensive': {
        'name': 'Compute Intensive',
        'description': 'Heavy mathematical operations - tests FPU throughput',
        'code': '''
import numpy as np
import time
n = 1000
A = np.random.rand(n, n)
start = time.time()
B = np.sin(A) * np.cos(A)
C = np.sqrt(np.abs(B))
D = np.log1p(C)
result = np.sum(D)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w6_branch_intensive': {
        'name': 'Branch Intensive',
        'description': 'Heavy branching - tests branch prediction',
        'code': '''
import random
import time
n = 50000
arr = [random.randint(1, 100) for _ in range(n)]
start = time.time()
result = 0
for x in arr:
    if x < 25:
        result += x * 2
    elif x < 50:
        result += x * 3
    elif x < 75:
        result += x * 4
    else:
        result += x * 5
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w7_cache_friendly': {
        'name': 'Cache Friendly',
        'description': 'Sequential access - tests cache hit rates',
        'code': '''
import numpy as np
import time
n = 5000
arr = np.random.rand(n, n)
start = time.time()
result = np.sum(arr, axis=1)
result = np.sum(result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'bandwidth']
    },
    
    'w8_mixed_workload': {
        'name': 'Mixed Workload',
        'description': 'Combines multiple patterns',
        'code': '''
import numpy as np
import time
n = 300
A = np.random.rand(n, n)
B = np.random.rand(n, n)
start = time.time()
C = np.dot(A, B)
D = np.sin(C) + np.cos(C)
E = np.sort(D.flatten())
result = np.sum(E[::10])
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    # Additional Workloads
    'w9_vector_ops': {
        'name': 'Vector Operations',
        'description': 'SIMD-friendly vector operations',
        'code': '''
import numpy as np
import time
n = 10000000
a = np.random.rand(n)
b = np.random.rand(n)
start = time.time()
c = a * b + np.sin(a) - np.cos(b)
result = np.sum(c)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w10_nested_loops': {
        'name': 'Nested Loops',
        'description': 'Deeply nested loops - tests instruction scheduling',
        'code': '''
import time
n = 200
start = time.time()
result = 0
for i in range(n):
    for j in range(n):
        for k in range(n):
            result += i * j + k
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w11_string_processing': {
        'name': 'String Processing',
        'description': 'String manipulation - tests integer ALU',
        'code': '''
import random
import string
import time
n = 100000
strings = [''.join(random.choices(string.ascii_letters, k=50)) for _ in range(n)]
start = time.time()
result = []
for s in strings:
    result.append(s.upper().replace('A', 'X').count('X'))
total = sum(result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w12_recursive': {
        'name': 'Recursive Algorithm',
        'description': 'Recursive computation - tests call stack and branch prediction',
        'code': '''
import time
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

start = time.time()
result = fibonacci(35)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w13_hash_table': {
        'name': 'Hash Table Operations',
        'description': 'Dictionary/hash operations - tests memory access patterns',
        'code': '''
import random
import time
n = 100000
data = {i: random.random() for i in range(n)}
keys = list(data.keys())
random.shuffle(keys)
start = time.time()
result = 0
for key in keys:
    if key in data:
        result += data[key]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'bandwidth']
    },
    
    'w14_matrix_decomp': {
        'name': 'Matrix Decomposition',
        'description': 'LU decomposition - tests numerical algorithms',
        'code': '''
import numpy as np
import time
n = 400
A = np.random.rand(n, n)
start = time.time()
P, L, U = np.linalg.lu(A)
result = np.sum(L) + np.sum(U)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'memory-access', 'microarchitecture-exploration', 'bandwidth']
    },
    
    'w15_pattern_matching': {
        'name': 'Pattern Matching',
        'description': 'String search - tests branch and memory patterns',
        'code': '''
import random
import string
import time
text = ''.join(random.choices(string.ascii_letters + ' ', k=1000000))
pattern = 'ABCDEFGH'
start = time.time()
count = text.count(pattern)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    # Additional Standard Workloads (SPEC-like, HPC, etc.)
    'w16_quicksort': {
        'name': 'Quick Sort',
        'description': 'Quicksort algorithm - tests branch prediction and cache behavior',
        'code': '''
import random
import time
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

n = 500000
arr = [random.randint(1, 1000000) for _ in range(n)]
start = time.time()
sorted_arr = quicksort(arr)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w17_linpack': {
        'name': 'LINPACK-like',
        'description': 'Dense linear algebra - tests FPU and memory bandwidth (HPC workload)',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'hpc-performance', 'bandwidth']
    },
    
    'w18_fft_2d': {
        'name': '2D FFT',
        'description': '2D Fast Fourier Transform - tests complex math and memory patterns',
        'code': '''
import numpy as np
import time
n = 1024
data = np.random.rand(n, n) + 1j * np.random.rand(n, n)
start = time.time()
result = np.fft.fft2(data)
result = np.fft.ifft2(result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'memory-access', 'microarchitecture-exploration', 'bandwidth']
    },
    
    'w19_monte_carlo': {
        'name': 'Monte Carlo Simulation',
        'description': 'Monte Carlo pi estimation - tests random number generation and FPU',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w20_sparse_matrix': {
        'name': 'Sparse Matrix Operations',
        'description': 'Sparse matrix-vector multiply - tests irregular memory access',
        'code': '''
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
''',
        'collection_types': ['memory-access', 'hotspots', 'bandwidth']
    },
    
    'w21_tree_traversal': {
        'name': 'Tree Traversal',
        'description': 'Binary tree operations - tests branch prediction and recursion',
        'code': '''
import random
import time
class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

def build_tree(n):
    root = Node(random.randint(1, 1000))
    for _ in range(n - 1):
        val = random.randint(1, 1000)
        node = root
        while True:
            if val < node.val:
                if node.left is None:
                    node.left = Node(val)
                    break
                node = node.left
            else:
                if node.right is None:
                    node.right = Node(val)
                    break
                node = node.right
    return root

def traverse(node, result):
    if node:
        traverse(node.left, result)
        result.append(node.val)
        traverse(node.right, result)

n = 100000
root = build_tree(n)
result = []
start = time.time()
traverse(root, result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w22_graph_bfs': {
        'name': 'Graph BFS',
        'description': 'Breadth-first search - tests memory access patterns and branch prediction',
        'code': '''
import random
import time
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited

# Build graph
n_nodes = 50000
graph = {}
for i in range(n_nodes):
    neighbors = random.sample(range(n_nodes), min(10, n_nodes))
    graph[i] = neighbors

start = time.time()
visited = bfs(graph, 0)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'microarchitecture-exploration']
    },
    
    'w23_image_processing': {
        'name': 'Image Processing',
        'description': 'Image convolution and filtering - tests SIMD and memory patterns',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'memory-access', 'bandwidth']
    },
    
    'w24_cryptographic': {
        'name': 'Cryptographic Hash',
        'description': 'SHA-256-like operations - tests integer ALU and bit operations',
        'code': '''
import hashlib
import time
import random
import string

n = 100000
data_list = [''.join(random.choices(string.ascii_letters + string.digits, k=100)) for _ in range(n)]
start = time.time()
hashes = []
for data in data_list:
    hash_obj = hashlib.sha256(data.encode())
    hashes.append(hash_obj.hexdigest())
result = len(set(hashes))
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w25_database_query': {
        'name': 'Database Query Simulation',
        'description': 'Join and aggregation operations - tests memory access and branch prediction',
        'code': '''
import random
import time

# Simulate database tables
n = 100000
table1 = [(i, random.randint(1, 1000), random.random()) for i in range(n)]
table2 = [(i, random.randint(1, 1000), random.random() * 100) for i in range(n)]

start = time.time()
# Hash join simulation
dict1 = {row[1]: row[2] for row in table1}
result = 0
for row in table2:
    key = row[1]
    if key in dict1:
        result += dict1[key] * row[2]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'microarchitecture-exploration']
    },
    
    'w26_nbody_simulation': {
        'name': 'N-Body Simulation',
        'description': 'Physics simulation - tests FPU and memory bandwidth (HPC workload)',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'hpc-performance', 'microarchitecture-exploration', 'bandwidth']
    },
    
    'w27_compression': {
        'name': 'Data Compression',
        'description': 'LZ-like compression - tests memory access and branch prediction',
        'code': '''
import time
import random
import string

def simple_compress(data):
    result = []
    i = 0
    while i < len(data):
        match_len = 0
        match_pos = 0
        for j in range(max(0, i - 1000), i):
            k = 0
            while i + k < len(data) and data[j + k] == data[i + k] and k < 255:
                k += 1
            if k > match_len:
                match_len = k
                match_pos = i - j
        if match_len > 3:
            result.append((match_pos, match_len))
            i += match_len
        else:
            result.append(data[i])
            i += 1
    return result

n = 50000
data = ''.join(random.choices(string.ascii_letters, k=n))
start = time.time()
compressed = simple_compress(data)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        'collection_types': ['memory-access', 'hotspots', 'microarchitecture-exploration']
    },
    
    'w28_neural_network': {
        'name': 'Neural Network Forward Pass',
        'description': 'Matrix operations for neural network - tests FPU and SIMD',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'memory-access', 'bandwidth']
    },
    
    'w29_particle_filter': {
        'name': 'Particle Filter',
        'description': 'Monte Carlo particle filter - tests random number generation and FPU',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
    
    'w30_ray_tracing': {
        'name': 'Ray Tracing',
        'description': 'Simple ray tracing - tests FPU, branch prediction, and memory',
        'code': '''
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
''',
        'collection_types': ['hotspots', 'microarchitecture-exploration', 'uarch-exploration']
    },
}


def get_all_workloads():
    """Get all available workload IDs."""
    return list(WORKLOADS.keys())


def get_workload_code(workload_id: str) -> str:
    """Get the Python code for a workload."""
    if workload_id in WORKLOADS:
        return WORKLOADS[workload_id]['code']
    raise ValueError(f"Workload {workload_id} not found")


def get_workload_info(workload_id: str) -> dict:
    """Get workload information."""
    if workload_id in WORKLOADS:
        return WORKLOADS[workload_id]
    raise ValueError(f"Workload {workload_id} not found")


def get_recommended_collection_types(workload_id: str) -> list:
    """Get recommended VTune collection types for a workload."""
    if workload_id in WORKLOADS:
        return WORKLOADS[workload_id].get('collection_types', ['hotspots'])
    return ['hotspots']


def list_all_workloads():
    """List all workloads with their descriptions."""
    print("Available Workloads:")
    print("=" * 70)
    for workload_id, info in WORKLOADS.items():
        print(f"{workload_id:20s}: {info['name']}")
        print(f"{'':20s}  {info['description']}")
        print(f"{'':20s}  Collection types: {', '.join(info['collection_types'])}")
        print()
