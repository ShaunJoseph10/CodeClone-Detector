"""Phase 3 tests: merge sort, binary search, BFS clusters, end-to-end CLI."""

import os
import random
import subprocess
import sys
import tempfile
import unittest

from codeclone.graph import build_graph, clusters, connected_components
from codeclone.ranking import above_threshold, merge_sort

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestRanking(unittest.TestCase):
    def test_merge_sort_descending(self):
        rng = random.Random(1)
        for n in (0, 1, 2, 7, 100):
            data = [rng.random() for _ in range(n)]
            self.assertEqual(merge_sort(data, key=lambda x: x), sorted(data, reverse=True))

    def test_merge_sort_stable(self):
        data = [(0.5, "a"), (0.9, "b"), (0.5, "c"), (0.5, "d")]
        self.assertEqual([x[1] for x in merge_sort(data, key=lambda x: x[0])], ["b", "a", "c", "d"])

    def test_binary_search_threshold(self):
        data = [0.95, 0.8, 0.6, 0.6, 0.59, 0.1]
        key = lambda x: x
        self.assertEqual(above_threshold(data, 0.6, key), [0.95, 0.8, 0.6, 0.6])
        self.assertEqual(above_threshold(data, 0.99, key), [])
        self.assertEqual(above_threshold(data, 0.0, key), data)
        self.assertEqual(above_threshold([], 0.5, key), [])


class TestGraph(unittest.TestCase):
    def test_clusters(self):
        # 0-1-2 chain (one cluster of 3), 3-4 pair, 5 alone
        adj = build_graph(6, [(0, 1), (1, 2), (3, 4)])
        self.assertEqual(len(connected_components(adj)), 3)
        self.assertEqual(sorted(sorted(c) for c in clusters(adj)), [[0, 1, 2], [3, 4]])


class TestEndToEnd(unittest.TestCase):
    def test_cli_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "report.html")
            result = subprocess.run(
                [sys.executable, "main.py", "dataset", "--threshold", "0.6", "--out", out],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Clusters:", result.stdout)
            with open(out) as f:
                page = f.read()
            self.assertIn("Ranked pairs", page)
            self.assertIn("p1_gcd_original.py", page)


if __name__ == "__main__":
    unittest.main()
