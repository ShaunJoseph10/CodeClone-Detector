def selection_sort(arr, n):
    for i in range(n):
        smallest = i
        for j in range(i + 1, n):
            if arr[j] < arr[smallest]:
                smallest = j
        hold = arr[i]
        arr[i] = arr[smallest]
        arr[smallest] = hold
    return arr

data = [64, 34, 25, 12, 22, 11, 90]
print(selection_sort(data, 7))
