def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)

def smallest_multiple(a, b):
    m = a
    while m % b != 0:
        m = m + a
    return m

print(gcd(48, 18))
print(smallest_multiple(4, 6))
