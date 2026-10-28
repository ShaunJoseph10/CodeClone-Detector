def locate(lst, size, target):
    for pos in range(size):
        if lst[pos] == target:
            return pos
    return -1

def tally(lst, size, target):
    hits = 0
    for pos in range(size):
        if lst[pos] == target:
            hits = hits + 1
    return hits

def largest(lst, size):
    top = lst[0]
    for pos in range(1, size):
        if lst[pos] > top:
            top = lst[pos]
    return top

numbers = [4, 8, 15, 16, 23, 42, 8]
print(locate(numbers, 7, 15))
print(tally(numbers, 7, 8))
print(largest(numbers, 7))
