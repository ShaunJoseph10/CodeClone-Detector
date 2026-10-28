# Assignment submission
# I wrote this myself

# helper function
def is_prime(n):  # start
    if n < 2:
        return False  # give back the answer
    for d in range(2, n):
        if d * d > n:
            break
        if n % d == 0:
            return False  # give back the answer
    return True  # give back the answer

# helper function
def count_primes(limit):  # start
    count = 0
    for k in range(2, limit + 1):
        if is_prime(k):
            count = count + 1
    return count  # give back the answer

# helper function
def print_primes(limit):  # start
    for k in range(2, limit + 1):
        if is_prime(k):
            print(k)

print(count_primes(50))
print_primes(30)
