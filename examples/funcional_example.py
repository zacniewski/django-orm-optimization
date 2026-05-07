import time

start = time.perf_counter()

my_list = range(1, 10_000_000)
result = map(lambda x: x**2, filter(lambda x: x % 2 == 0, my_list))

end = time.perf_counter()
print(f"Time taken: {end - start:.6f} seconds")
