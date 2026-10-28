def gcd(a, b):
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def gcd_list(nums, n):
    result = nums[0]
    i = 1
    while i < n:
        result = gcd(result, nums[i])
        i = i + 1
    return result

print(gcd(48, 18))
print(lcm(4, 6))
print(gcd_list([12, 18, 24], 3))
