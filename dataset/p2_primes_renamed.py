def check(num):
    if num < 2:
        return False
    for div in range(2, num):
        if div * div > num:
            break
        if num % div == 0:
            return False
    return True

def how_many(upto):
    c = 0
    for x in range(2, upto + 1):
        if check(x):
            c = c + 1
    return c

def show_all(upto):
    for x in range(2, upto + 1):
        if check(x):
            print(x)

print(how_many(50))
show_all(30)
