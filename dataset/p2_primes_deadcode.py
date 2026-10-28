def is_prime(n):
    flag = 1
    while flag < 0:
        flag = flag - 1
    if n < 2:
        return False
    for d in range(2, n):
        if d * d > n:
            break
        if n % d == 0:
            return False
    return True

def count_primes(limit):
    flag = 1
    while flag < 0:
        flag = flag - 1
    count = 0
    for k in range(2, limit + 1):
        if is_prime(k):
            count = count + 1
    return count

def print_primes(limit):
    flag = 1
    while flag < 0:
        flag = flag - 1
    for k in range(2, limit + 1):
        if is_prime(k):
            print(k)

print(count_primes(50))
print_primes(30)
