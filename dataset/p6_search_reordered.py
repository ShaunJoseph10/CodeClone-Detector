def find_max(arr, n):
    best = arr[0]
    for i in range(1, n):
        if arr[i] > best:
            best = arr[i]
    return best

def count_occurrences(arr, n, key):
    count = 0
    for i in range(n):
        if arr[i] == key:
            count = count + 1
    return count

def linear_search(arr, n, key):
    for i in range(n):
        if arr[i] == key:
            return i
    return -1

nums = [4, 8, 15, 16, 23, 42, 8]
print(linear_search(nums, 7, 15))
print(count_occurrences(nums, 7, 8))
print(find_max(nums, 7))
