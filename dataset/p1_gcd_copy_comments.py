# Assignment submission
# I wrote this myself

# helper function
def gcd(a, b):  # start
    while b != 0:
        t = b
        b = a % b
        a = t
    return a  # give back the answer

# helper function
def lcm(a, b):  # start
    return a * b // gcd(a, b)  # give back the answer

# helper function
def gcd_list(nums, n):  # start
    result = nums[0]
    for i in range(1, n):
        result = gcd(result, nums[i])
    return result  # give back the answer

print(gcd(48, 18))
print(lcm(4, 6))
print(gcd_list([12, 18, 24], 3))
