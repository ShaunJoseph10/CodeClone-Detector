def fibo(count):
    prev = 0
    curr = 1
    for step in range(count):
        nxt = prev + curr
        prev = curr
        curr = nxt
    return prev

def add_fibos(count):
    acc = 0
    for step in range(count):
        acc = acc + fibo(step)
    return acc

def list_fibos(count):
    for step in range(count):
        print(fibo(step))

print(fibo(10))
print(add_fibos(10))
list_fibos(8)
