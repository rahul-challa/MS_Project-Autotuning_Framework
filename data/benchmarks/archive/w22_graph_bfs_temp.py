
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
