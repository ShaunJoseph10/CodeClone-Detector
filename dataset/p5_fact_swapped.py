def factorial(n):
    result = 1
    for i in range(2, 1 + n):
        result = i * result
    return result

def ncr(n, r):
    return factorial(n) // (factorial(n - r) * factorial(r))

def pascal_row(n):
    for r in range(1 + n):
        print(ncr(n, r))

print(factorial(6))
print(ncr(5, 2))
pascal_row(5)
