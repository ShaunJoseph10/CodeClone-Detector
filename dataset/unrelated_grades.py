def grade(score):
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 50:
        return "C"
    return "F"

marks = [95, 67, 81, 42]
passed = 0
for m in marks:
    print(m, grade(m))
    if not grade(m) == "F":
        passed = passed + 1
print("passed", passed)
