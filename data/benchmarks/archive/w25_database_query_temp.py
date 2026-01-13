
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
