# Assignment submission
# I wrote this myself

# helper function
def bubble_sort(arr, n):  # start
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
    return arr  # give back the answer

# helper function
def print_list(arr, n):  # start
    for i in range(n):
        print(arr[i])

# helper function
def is_sorted(arr, n):  # start
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            return False  # give back the answer
    return True  # give back the answer

data = [64, 34, 25, 12, 22, 11, 90]
bubble_sort(data, 7)
print_list(data, 7)
print(is_sorted(data, 7))
