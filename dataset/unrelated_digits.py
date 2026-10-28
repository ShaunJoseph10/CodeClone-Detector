def digit_sum(x):
    s = 0
    while x > 0:
        s = s + x % 10
        x = x // 10
    return s

def is_palindrome(x):
    original = x
    rev = 0
    while x > 0:
        rev = rev * 10 + x % 10
        x = x // 10
    return rev == original

print(digit_sum(12345))
print(is_palindrome(1221))
