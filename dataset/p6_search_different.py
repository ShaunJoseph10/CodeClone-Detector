def binary_search(arr, key):
    lo = 0
    hi = len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == key:
            return mid
        if arr[mid] < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

sorted_nums = [4, 8, 15, 16, 23, 42]
print(binary_search(sorted_nums, 23))
