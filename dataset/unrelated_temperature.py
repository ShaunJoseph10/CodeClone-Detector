def to_fahrenheit(c):
    return c * 9 / 5 + 32

def describe(f):
    if f > 86:
        return "hot"
    elif f > 59:
        return "mild"
    return "cold"

celsius = 0
while celsius <= 40:
    print(celsius, describe(to_fahrenheit(celsius)))
    celsius = celsius + 10
