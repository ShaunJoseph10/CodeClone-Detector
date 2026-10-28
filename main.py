"""CodeClone Detector command line.

    python main.py <folder_of_.py_submissions> --threshold 0.6 --min-mass 6
"""

import argparse
import os
import sys

from codeclone.graph import build_graph, clusters
from codeclone.lexer import LexerError
from codeclone.matcher import MIN_MASS, SourceFile, find_clones
from codeclone.parser import ParseError
from codeclone.ranking import above_threshold, merge_sort
from codeclone.report import print_summary, write_html
from codeclone.scorer import similarity


class Pair:
    def __init__(self, file_a, file_b, clones):
        self.file_a, self.file_b, self.clones = file_a, file_b, clones
        self.score = similarity(file_a, file_b, clones)


def load_folder(folder):
    """Read every .py file in the folder (sorted by name). Files that fail to parse are skipped."""
    files = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(folder, name)) as f:
            source = f.read()
        try:
            files.append(SourceFile(len(files), name, source))
        except (LexerError, ParseError) as e:
            print("skipping %s: %s" % (name, e), file=sys.stderr)
    return files


def analyze(files, min_mass=MIN_MASS):
    """Match all files, score every pair, return the pairs ranked by similarity (descending)."""
    clones = find_clones(files, min_mass)
    by_pair = [[[] for _ in files] for _ in files]  # by_pair[i][j]: clones between file i and j (i < j)
    for c in clones:
        by_pair[c.file_a.id][c.file_b.id].append(c)
    pairs = [Pair(files[i], files[j], by_pair[i][j])
             for i in range(len(files)) for j in range(i + 1, len(files))]
    return merge_sort(pairs, key=lambda p: p.score)   # CO5: merge sort


def main():
    ap = argparse.ArgumentParser(description="Detect copied code between Python submissions.")
    ap.add_argument("folder")
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-mass", type=int, default=MIN_MASS)
    ap.add_argument("--out", default="report.html")
    args = ap.parse_args()

    if not os.path.isdir(args.folder):
        sys.exit("not a folder: %s" % args.folder)
    files = load_folder(args.folder)
    if len(files) < 2:
        sys.exit("need at least 2 parsable .py files")

    ranked = analyze(files, args.min_mass)
    flagged = above_threshold(ranked, args.threshold, key=lambda p: p.score)   # CO5: binary search
    groups = clusters(build_graph(len(files), [(p.file_a.id, p.file_b.id) for p in flagged]))  # CO5: BFS

    write_html(args.out, files, ranked, flagged, groups, args.threshold)
    print_summary(files, flagged, groups, args.threshold)
    print("Report written to %s" % args.out)


if __name__ == "__main__":
    main()
