def factorial(n):
    result = 1
    i = 2
    while i < n + 1:
        result = result * i
        i = i + 1
    return result

def ncr(n, r):
    return factorial(n) // (factorial(r) * factorial(n - r))

def pascal_row(n):
    r = 0
    while r < n + 1:
        print(ncr(n, r))
        r = r + 1

print(factorial(6))
print(ncr(5, 2))
pascal_row(5)
