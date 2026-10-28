def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result = result * i
    return result

def ncr(n, r):
    return factorial(n) // (factorial(r) * factorial(n - r))

def pascal_row(n):
    for r in range(n + 1):
        print(ncr(n, r))

print(factorial(6))
print(ncr(5, 2))
pascal_row(5)
