"""Phase 2 tests: normalizer, hasher, hash table, matcher, scorer."""

import unittest

from codeclone.hashtable import HashTable
from codeclone.matcher import SourceFile, find_clones, structurally_equal
from codeclone.parser import parse
from codeclone.scorer import similarity
from codeclone.hasher import hash_tree
from codeclone.normalizer import normalize

ORIGINAL = """
def gcd(a, b):
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

def lcm(a, b):
    return a * b // gcd(a, b)

def total(n):
    s = 0
    i = 1
    while i <= n:
        s = s + i * 2
        i = i + 1
    return s

print(gcd(48, 18), lcm(4, 6), total(10))
"""

RENAMED = """
def great_divisor(x, y):
    while y != 0:
        tmp = y
        y = x % y
        x = tmp
    return x

def least_mult(x, y):
    return x * y // great_divisor(x, y)

def add_up(limit):
    acc = 0
    k = 1
    while k <= limit:
        acc = acc + k * 2
        k = k + 1
    return acc

print(great_divisor(48, 18), least_mult(4, 6), add_up(10))
"""

REORDERED = """
def total(n):
    s = 0
    i = 1
    while i <= n:
        s = s + i * 2
        i = i + 1
    return s

def lcm(a, b):
    return a * b // gcd(a, b)

def gcd(a, b):
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

print(gcd(48, 18), lcm(4, 6), total(10))
"""

SWAPPED = """
def gcd(a, b):
    while 0 != b:
        t = b
        b = a % b
        a = t
    return a

def lcm(a, b):
    return b * a // gcd(a, b)

def total(n):
    s = 0
    i = 1
    while i <= n:
        s = 2 * i + s
        i = 1 + i
    return s

print(gcd(48, 18), lcm(4, 6), total(10))
"""

COMMENTED = """
# Utility functions for my homework
def gcd(a, b):   # Euclid
    while b != 0:
        t = b      # remember b
        b = a % b
        a = t

    return a

# lcm uses gcd
def lcm(a, b):
    return a * b // gcd(a, b)

def total(n):
    s = 0
    i = 1
    # loop over 1..n
    while i <= n:
        s = s + i * 2
        i = i + 1
    return s

print(gcd(48, 18), lcm(4, 6), total(10))
"""

UNRELATED = """
def bubble(arr, n):
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
    return arr

def show(arr):
    for x in arr:
        if x % 2 == 0:
            print("even", x)
        else:
            print("odd", x)

data = [5, 1, 4, 2, 8]
show(bubble(data, 5))
"""


def score(src_a, src_b, min_mass=6):
    a, b = SourceFile(0, "a.py", src_a), SourceFile(1, "b.py", src_b)
    return similarity(a, b, find_clones([a, b], min_mass))


class TestDetection(unittest.TestCase):
    def test_exact_copy(self):
        self.assertAlmostEqual(score(ORIGINAL, ORIGINAL), 1.0)

    def test_renamed_variables(self):
        self.assertAlmostEqual(score(ORIGINAL, RENAMED), 1.0)

    def test_reordered_functions(self):
        self.assertGreater(score(ORIGINAL, REORDERED), 0.9)

    def test_swapped_operands(self):
        self.assertAlmostEqual(score(ORIGINAL, SWAPPED), 1.0)

    def test_extra_comments(self):
        self.assertAlmostEqual(score(ORIGINAL, COMMENTED), 1.0)

    def test_unrelated_scores_low(self):
        self.assertLess(score(ORIGINAL, UNRELATED), 0.2)


class TestCore(unittest.TestCase):
    def test_commutative_hash(self):
        a = hash_tree(normalize(parse("x = a + b\n")))
        b = hash_tree(normalize(parse("x = b + a\n")))
        c = hash_tree(normalize(parse("x = a - b\n")))
        self.assertEqual(a.hash, b.hash)
        self.assertNotEqual(a.hash, c.hash)

    def test_mirrored_comparison(self):
        a = hash_tree(normalize(parse("x = n > 1\n")))
        b = hash_tree(normalize(parse("x = 1 < n\n")))
        c = hash_tree(normalize(parse("x = n < 1\n")))
        self.assertEqual(a.hash, b.hash)
        self.assertNotEqual(a.hash, c.hash)

    def test_size(self):
        root = hash_tree(normalize(parse("x = a + 1\n")))
        # Module -> Assign -> [Name, BinOp -> [Name, Num]] = 6 nodes
        self.assertEqual(root.size, 6)

    def test_structural_check_rejects_forced_collision(self):
        a = hash_tree(normalize(parse("x = a + 1\n")))
        b = hash_tree(normalize(parse("x = a * 1\n")))
        b.hash = a.hash  # pretend the fingerprints collided
        self.assertFalse(structurally_equal(a, b))

    def test_maximal_only(self):
        a, b = SourceFile(0, "a", ORIGINAL), SourceFile(1, "b", ORIGINAL)
        clones = find_clones([a, b])
        self.assertEqual(len(clones), 1)  # the whole Module, none of its sub-parts
        self.assertEqual(clones[0].node_a.label, "Module")

    def test_hashtable_chaining_and_rehash(self):
        t = HashTable(capacity=4)
        for i in range(10):
            t.insert(i * 4, "f", i)  # all land in one bucket before rehashing
        self.assertGreater(t.capacity, 4)
        self.assertLessEqual(t.load_factor(), 0.75)
        self.assertEqual(t.count, 10)
        self.assertEqual([e.node for e in t.get_bucket(8)], [2])
        self.assertEqual(sum(len(c) for c in t.chains()), 10)


if __name__ == "__main__":
    unittest.main()
