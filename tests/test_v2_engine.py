"""v2 engine tests: dead code, loop canonicalization, LCS, winnowing, index, API."""

import json
import unittest

from codeclone.api import Config, analyze
from codeclone.deadcode import remove_dead_code
from codeclone.hasher import hash_tree
from codeclone.hashtable import HashMap, HashSet
from codeclone.index import candidate_pairs
from codeclone.matcher import SourceFile
from codeclone.normalizer import canonicalize, normalize
from codeclone.parser import parse
from codeclone.scorer import lcs_length, lcs_similarity
from codeclone.winnow import fingerprint_set, fingerprints, kgram_hashes, token_stream, winnow_similarity

PASSES = (remove_dead_code, canonicalize)


def tree(src, passes=PASSES):
    root = parse(src)
    for p in passes:
        root = p(root)
    return hash_tree(normalize(root))


def same(a, b):
    return tree(a).hash == tree(b).hash


class TestHashMap(unittest.TestCase):
    def test_put_get_remove_grow(self):
        m = HashMap(capacity=2)
        for i in range(50):
            m.put(("k", i), i * i)
        self.assertEqual(len(m), 50)
        self.assertGreater(m.capacity, 2)
        self.assertEqual(m.get(("k", 7)), 49)
        m.put(("k", 7), -1)
        self.assertEqual(m.get(("k", 7)), -1)
        m.remove(("k", 7))
        self.assertNotIn(("k", 7), m)
        self.assertEqual(len(m), 49)

    def test_set(self):
        s = HashSet(["a", "b"])
        s.add("a")
        self.assertEqual(sorted(s), ["a", "b"])
        t = s.copy()
        t.discard("a")
        self.assertIn("a", s)
        self.assertNotIn("a", t)


class TestDeadCode(unittest.TestCase):
    BODY = "def f(a):\n    s = a * 2\n    return s\n"

    def test_if_false_removed(self):
        self.assertTrue(same(self.BODY, "def f(a):\n    if False:\n        print(1)\n    s = a * 2\n    return s\n"))

    def test_if_false_keeps_else(self):
        self.assertTrue(same("x = 1\nprint(x)\n", "if False:\n    x = 2\nelse:\n    x = 1\nprint(x)\n"))

    def test_unreachable_after_return(self):
        self.assertTrue(same(self.BODY, "def f(a):\n    s = a * 2\n    return s\n    print(s)\n"))

    def test_constant_guard_and_dead_store(self):
        # the dataset's disguise: a constant flag guarding code that never runs
        junk = ("def f(a):\n    extra = 3\n    extra = extra * 2\n    if extra > 100:\n"
                "        print(\"overflow\")\n    s = a * 2\n    return s\n")
        self.assertTrue(same(self.BODY, junk))

    def test_while_false_on_entry_removed(self):
        junk = "def f(a):\n    seen = 0\n    while seen > 10:\n        seen = seen + 1\n    s = a * 2\n    return s\n"
        self.assertTrue(same(self.BODY, junk))

    def test_len_of_literal_list(self):
        junk = "def f(a):\n    w = [0, 0]\n    if len(w) > 5:\n        print(w)\n    s = a * 2\n    return s\n"
        self.assertTrue(same(self.BODY, junk))

    def test_live_and_side_effects_kept(self):
        # x is read later, and g() may have side effects: neither may be removed
        src = "def f(a):\n    x = a + 1\n    y = g(a)\n    return x\n"
        self.assertFalse(same("def f(a):\n    return a + 1\n", src))
        body = tree(src).children[0].children[1]
        self.assertEqual(len(body.children), 3)

    def test_loop_carried_value_kept(self):
        src = "def f(n):\n    s = 0\n    i = 0\n    while i < n:\n        s = s + i\n        i = i + 1\n    return s\n"
        body = tree(src).children[0].children[1]
        self.assertEqual(len(body.children), 4)

    def test_unknown_condition_kept(self):
        src = "def f(a):\n    if a > 100:\n        print(a)\n    return a\n"
        self.assertEqual(len(tree(src).children[0].children[1].children), 2)


class TestLoops(unittest.TestCase):
    def test_for_range_equals_while(self):
        a = "def f(n):\n    s = 0\n    for i in range(1, n):\n        s = s + i\n    return s\n"
        b = "def f(n):\n    s = 0\n    i = 1\n    while i < n:\n        s = s + i\n        i = i + 1\n    return s\n"
        self.assertTrue(same(a, b))

    def test_range_one_arg_and_augassign(self):
        a = "for i in range(n):\n    print(i)\n"
        b = "i = 0\nwhile i < n:\n    print(i)\n    i += 1\n"
        self.assertTrue(same(a, b))

    def test_negative_step(self):
        a = "for i in range(n, 0, -1):\n    print(i)\n"
        b = "i = n\nwhile i > 0:\n    print(i)\n    i = i - 1\n"
        self.assertTrue(same(a, b))

    def test_continue_not_rewritten(self):
        root = tree("for i in range(n):\n    if i == 2:\n        continue\n    print(i)\n")
        self.assertEqual(root.children[0].label, "For")

    def test_non_range_not_rewritten(self):
        self.assertEqual(tree("for x in items:\n    print(x)\n").children[0].label, "For")

    def test_v1_unchanged_without_passes(self):
        a = "for i in range(n):\n    print(i)\n"
        b = "i = 0\nwhile i < n:\n    print(i)\n    i = i + 1\n"
        self.assertNotEqual(tree(a, ()).hash, tree(b, ()).hash)


class TestLCS(unittest.TestCase):
    def test_lcs_length(self):
        self.assertEqual(lcs_length("ABCBDAB", "BDCABA"), 4)
        self.assertEqual(lcs_length([], [1, 2]), 0)
        self.assertEqual(lcs_length([1, 2, 3], [1, 2, 3]), 3)

    def test_junk_lines_tolerated(self):
        # print() calls have side effects, so dead-code removal cannot delete them; LCS copes
        a = "def f(n):\n    s = 0\n    i = 0\n    while i < n:\n        s = s + i\n        i = i + 1\n    return s\n"
        b = ("def f(n):\n    print(\"start\")\n    s = 0\n    i = 0\n    while i < n:\n        print(\"x\")\n"
             "        s = s + i\n        i = i + 1\n    return s\n")
        fa, fb = SourceFile(0, "a", a, PASSES), SourceFile(1, "b", b, PASSES)
        self.assertGreater(lcs_similarity(fa, fb), 0.85)


class TestWinnow(unittest.TestCase):
    def test_rolling_hash_matches_direct(self):
        from codeclone.hasher import M, P
        toks = token_stream(tree("x = a + b * c\nprint(x)\n"))
        grams = kgram_hashes(toks, 3)
        for i, (h, _) in enumerate(grams):
            direct = 0
            for t, _ in toks[i:i + 3]:
                direct = (direct * P + t) % M
            self.assertEqual(h, direct)

    def test_identical_and_renamed(self):
        a = fingerprint_set(fingerprints(tree("def f(a, b):\n    return a * b + 1\nprint(f(2, 3))\n")))
        b = fingerprint_set(fingerprints(tree("def g(x, y):\n    return y * x + 1\nprint(g(2, 3))\n")))
        self.assertEqual(winnow_similarity(a, b), 1.0)

    def test_short_input(self):
        self.assertEqual(len(fingerprints(tree("x = 1\n"))), 1)


class TestIndex(unittest.TestCase):
    def test_candidates(self):
        sets = [HashSet([1, 2, 3, 4]), HashSet([1, 2, 3, 9]), HashSet([7, 8, 9])]
        pairs, ignored = candidate_pairs(sets, min_shared=3, max_df=1.0)
        self.assertEqual(pairs, [(0, 1)])
        self.assertEqual(ignored, 0)

    def test_common_fingerprints_ignored(self):
        sets = [HashSet([1, 10]), HashSet([1, 11]), HashSet([1, 12]), HashSet([1, 13])]
        pairs, ignored = candidate_pairs(sets, min_shared=1, max_df=0.5)
        self.assertEqual(pairs, [])
        self.assertEqual(ignored, 1)


class TestAPI(unittest.TestCase):
    A = "def gcd(a, b):\n    while b != 0:\n        t = b\n        b = a % b\n        a = t\n    return a\nprint(gcd(4, 6))\n"
    B = "def h(x, y):\n    while y != 0:\n        z = y\n        y = x % y\n        x = z\n    return x\nprint(h(4, 6))\n"
    C = "names = ['a', 'b']\nfor n in names:\n    print('hello', n)\n"

    def test_analyze(self):
        r = analyze([("a.py", self.A), ("b.py", self.B), ("c.py", self.C), ("bad.py", "def (:\n")])
        self.assertIn("bad.py", r.errors)
        self.assertEqual(r.files, ["a.py", "b.py", "c.py"])
        self.assertEqual((r.pairs[0].a, r.pairs[0].b), ("a.py", "b.py"))
        self.assertGreater(r.pairs[0].score, 0.95)
        self.assertEqual(set(r.pairs[0].signals), {"dice", "containment", "lcs", "winnow"})
        self.assertTrue(r.pairs[0].matches)
        self.assertEqual(r.clusters, [["a.py", "b.py"]])
        self.assertEqual(r.stats["total_pairs"], 3)
        self.assertEqual(r.stats["pairs_scored"] + r.stats["pairs_skipped"], 3)
        data = json.loads(r.to_json())
        self.assertEqual(data["pairs"][0]["matches"][0]["a_start"], 1)

    def test_v1_config_scores_all_pairs(self):
        r = analyze([("a.py", self.A), ("b.py", self.B), ("c.py", self.C)], Config.v1())
        self.assertEqual(r.stats["pairs_scored"], 3)
        self.assertEqual(r.stats["pairs_skipped"], 0)

    def test_empty_and_single(self):
        self.assertEqual(analyze([]).pairs, [])
        self.assertEqual(analyze([("a.py", self.A)]).stats["total_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
