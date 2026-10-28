def fact(m):
    prod = 1
    for j in range(2, m + 1):
        prod = prod * j
    return prod

def choose(m, k):
    return fact(m) // (fact(k) * fact(m - k))

def row_of(m):
    for k in range(m + 1):
        print(choose(m, k))

print(fact(6))
print(choose(5, 2))
row_of(5)
