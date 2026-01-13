
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
