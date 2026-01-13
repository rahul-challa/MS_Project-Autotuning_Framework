
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
