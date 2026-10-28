def hcf(first, second):
    while second != 0:
        keep = second
        second = first % second
        first = keep
    return first

def least_common(first, second):
    return first * second // hcf(first, second)

def hcf_many(values, size):
    answer = values[0]
    for idx in range(1, size):
        answer = hcf(answer, values[idx])
    return answer

print(hcf(48, 18))
print(least_common(4, 6))
print(hcf_many([12, 18, 24], 3))
