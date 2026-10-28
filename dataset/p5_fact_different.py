def choose(n, r):
    num = 1
    den = 1
    k = 1
    while k <= r:
        num = num * (n - k + 1)
        den = den * k
        k = k + 1
    return num // den

print(choose(5, 2))
print(choose(10, 3))
