# Assignment submission
# I wrote this myself

# helper function
def factorial(n):  # start
    result = 1
    for i in range(2, n + 1):
        result = result * i
    return result  # give back the answer

# helper function
def ncr(n, r):  # start
    return factorial(n) // (factorial(r) * factorial(n - r))  # give back the answer

# helper function
def pascal_row(n):  # start
    for r in range(n + 1):
        print(ncr(n, r))

print(factorial(6))
print(ncr(5, 2))
pascal_row(5)
