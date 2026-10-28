def linear_search(arr, n, key):
    i = 0
    while i < n:
        if arr[i] == key:
            return i
        i = i + 1
    return -1

def count_occurrences(arr, n, key):
    count = 0
    i = 0
    while i < n:
        if arr[i] == key:
            count = count + 1
        i = i + 1
    return count

def find_max(arr, n):
    best = arr[0]
    i = 1
    while i < n:
        if arr[i] > best:
            best = arr[i]
        i = i + 1
    return best

nums = [4, 8, 15, 16, 23, 42, 8]
print(linear_search(nums, 7, 15))
print(count_occurrences(nums, 7, 8))
print(find_max(nums, 7))
