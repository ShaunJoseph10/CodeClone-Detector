# Assignment submission
# I wrote this myself

# helper function
def linear_search(arr, n, key):  # start
    for i in range(n):
        if arr[i] == key:
            return i  # give back the answer
    return -1  # give back the answer

# helper function
def count_occurrences(arr, n, key):  # start
    count = 0
    for i in range(n):
        if arr[i] == key:
            count = count + 1
    return count  # give back the answer

# helper function
def find_max(arr, n):  # start
    best = arr[0]
    for i in range(1, n):
        if arr[i] > best:
            best = arr[i]
    return best  # give back the answer

nums = [4, 8, 15, 16, 23, 42, 8]
print(linear_search(nums, 7, 15))
print(count_occurrences(nums, 7, 8))
print(find_max(nums, 7))
