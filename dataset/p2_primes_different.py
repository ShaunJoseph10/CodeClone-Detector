def sieve(limit):
    marks = [True] * (limit + 1)
    marks[0] = False
    marks[1] = False
    p = 2
    while p * p <= limit:
        if marks[p]:
            m = p * p
            while m <= limit:
                marks[m] = False
                m = m + p
        p = p + 1
    return marks

table = sieve(50)
total = 0
for v in range(51):
    if table[v]:
        total = total + 1
print(total)
