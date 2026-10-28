def sort_it(items, length):
    for p in range(length):
        for q in range(0, length - p - 1):
            if items[q] > items[q + 1]:
                swap = items[q]
                items[q] = items[q + 1]
                items[q + 1] = swap
    return items

def display(items, length):
    for p in range(length):
        print(items[p])

def in_order(items, length):
    for p in range(length - 1):
        if items[p] > items[p + 1]:
            return False
    return True

marks = [64, 34, 25, 12, 22, 11, 90]
sort_it(marks, 7)
display(marks, 7)
print(in_order(marks, 7))
