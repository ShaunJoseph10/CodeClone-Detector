def print_primes(limit):
    for k in range(2, limit + 1):
        if is_prime(k):
            print(k)

def count_primes(limit):
    count = 0
    for k in range(2, limit + 1):
        if is_prime(k):
            count = count + 1
    return count

def is_prime(n):
    if n < 2:
        return False
    for d in range(2, n):
        if d * d > n:
            break
        if n % d == 0:
            return False
    return True

print(count_primes(50))
print_primes(30)
