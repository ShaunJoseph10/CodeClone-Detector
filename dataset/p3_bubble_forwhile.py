def bubble_sort(arr, n):
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            j = j + 1
        i = i + 1
    return arr

def print_list(arr, n):
    i = 0
    while i < n:
        print(arr[i])
        i = i + 1

def is_sorted(arr, n):
    i = 0
    while i < n - 1:
        if arr[i] > arr[i + 1]:
            return False
        i = i + 1
    return True

data = [64, 34, 25, 12, 22, 11, 90]
bubble_sort(data, 7)
print_list(data, 7)
print(is_sorted(data, 7))
