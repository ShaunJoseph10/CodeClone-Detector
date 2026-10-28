def bubble_sort(arr, n):
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
    return arr

def print_list(arr, n):
    for i in range(n):
        print(arr[i])

def is_sorted(arr, n):
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True

data = [64, 34, 25, 12, 22, 11, 90]
bubble_sort(data, 7)
print_list(data, 7)
print(is_sorted(data, 7))
