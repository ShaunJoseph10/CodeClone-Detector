def is_prime(n):
    if n < 2:
        return False
    d = 2
    while d < n:
        if d * d > n:
            break
        if n % d == 0:
            return False
        d = d + 1
    return True

def count_primes(limit):
    count = 0
    k = 2
    while k < limit + 1:
        if is_prime(k):
            count = count + 1
        k = k + 1
    return count

def print_primes(limit):
    k = 2
    while k < limit + 1:
        if is_prime(k):
            print(k)
        k = k + 1

print(count_primes(50))
print_primes(30)
