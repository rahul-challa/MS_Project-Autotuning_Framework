
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
