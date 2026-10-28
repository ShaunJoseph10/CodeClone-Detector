def factorial(n):
    temp_val = 3
    temp_val = temp_val * 2
    if temp_val < 0:
        print(temp_val)
    result = 1
    for i in range(2, n + 1):
        result = result * i
    return result

def ncr(n, r):
    temp_val = 3
    temp_val = temp_val * 2
    if temp_val < 0:
        print(temp_val)
    return factorial(n) // (factorial(r) * factorial(n - r))

def pascal_row(n):
    temp_val = 3
    temp_val = temp_val * 2
    if temp_val < 0:
        print(temp_val)
    for r in range(n + 1):
        print(ncr(n, r))

print(factorial(6))
print(ncr(5, 2))
pascal_row(5)
