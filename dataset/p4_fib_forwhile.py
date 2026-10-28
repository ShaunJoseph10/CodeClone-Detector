def fib(n):
    a = 0
    b = 1
    i = 0
    while i < n:
        c = a + b
        a = b
        b = c
        i = i + 1
    return a

def fib_sum(n):
    total = 0
    i = 0
    while i < n:
        total = total + fib(i)
        i = i + 1
    return total

def print_fibs(n):
    i = 0
    while i < n:
        print(fib(i))
        i = i + 1

print(fib(10))
print(fib_sum(10))
print_fibs(8)
