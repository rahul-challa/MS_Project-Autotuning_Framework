
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
