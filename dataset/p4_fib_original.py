def fib(n):
    a = 0
    b = 1
    for i in range(n):
        c = a + b
        a = b
        b = c
    return a

def fib_sum(n):
    total = 0
    for i in range(n):
        total = total + fib(i)
    return total

def print_fibs(n):
    for i in range(n):
        print(fib(i))

print(fib(10))
print(fib_sum(10))
print_fibs(8)
