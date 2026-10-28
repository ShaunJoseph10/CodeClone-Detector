def is_prime(n):
    if n < 2:
        return False
    for d in range(2, n):
        if n < d * d:
            break
        if n % d == 0:
            return False
    return True

def count_primes(limit):
    count = 0
    for k in range(2, 1 + limit):
        if is_prime(k):
            count = 1 + count
    return count

def print_primes(limit):
    for k in range(2, 1 + limit):
        if is_prime(k):
            print(k)

print(count_primes(50))
print_primes(30)
