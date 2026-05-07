import time

start = time.perf_counter()

my_list = range(1, 10_000_000)
for i in my_list:
    if i % 2 == 0:
        result = i**2

end = time.perf_counter()
print(f"Time taken: {end - start:.6f} seconds")
