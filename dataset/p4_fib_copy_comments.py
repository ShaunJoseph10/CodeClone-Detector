# Assignment submission
# I wrote this myself

# helper function
def fib(n):  # start
    a = 0
    b = 1
    for i in range(n):
        c = a + b
        a = b
        b = c
    return a  # give back the answer

# helper function
def fib_sum(n):  # start
    total = 0
    for i in range(n):
        total = total + fib(i)
    return total  # give back the answer

# helper function
def print_fibs(n):  # start
    for i in range(n):
        print(fib(i))

print(fib(10))
print(fib_sum(10))
print_fibs(8)
