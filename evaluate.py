"""Evaluate the detector on dataset/: precision/recall per threshold and running time.

Ground truth comes from file names: pX_<program>_<variant>.py.
Two files are a true plagiarism pair when they share the same program prefix and neither is
the "different" variant (a different algorithm for the same task is not a copy).
"""

import time

from main import analyze, load_folder
from codeclone.matcher import SourceFile
from codeclone.ranking import above_threshold

DATASET = "dataset"


def program_of(name):
    """'p3_bubble_renamed.py' -> 'p3_bubble'; unrelated or 'different' files -> None."""
    if not name.startswith("p") or name.endswith("_different.py"):
        return None
    return "_".join(name.split("_")[:2])


def is_plagiarism(pair):
    a, b = program_of(pair.file_a.name), program_of(pair.file_b.name)
    return a is not None and a == b


def accuracy_table(ranked):
    positives = sum(1 for p in ranked if is_plagiarism(p))
    print("Pairs: %d total, %d true plagiarism pairs" % (len(ranked), positives))
    print("threshold  flagged  TP   FP   FN   precision  recall")
    for t in (0.4, 0.5, 0.6, 0.7, 0.8):
        flagged = above_threshold(ranked, t, key=lambda p: p.score)
        tp = sum(1 for p in flagged if is_plagiarism(p))
        fp = len(flagged) - tp
        fn = positives - tp
        precision = tp / len(flagged) if flagged else 1.0
        recall = tp / positives if positives else 1.0
        print("   %.1f     %4d   %4d %4d %4d     %.3f     %.3f" % (t, len(flagged), tp, fp, fn, precision, recall))


def recall_by_variant(ranked):
    """Detection rate of each variant against its own original, at threshold 0.6."""
    print("\nOriginal vs variant at threshold 0.6 (detected / total):")
    stats = {}
    for p in ranked:
        names = (p.file_a.name, p.file_b.name)
        if not is_plagiarism(p) or not any(n.endswith("_original.py") for n in names):
            continue
        other = names[1] if names[0].endswith("_original.py") else names[0]
        variant = other[:-3].split("_", 2)[2]
        hit, total = stats.get(variant, (0, 0))
        stats[variant] = (hit + (p.score >= 0.6), total + 1)
    for variant, (hit, total) in stats.items():
        print("  %-14s %d / %d" % (variant, hit, total))


def timing(files):
    """Running time vs number of files. Larger inputs are made by repeating the dataset."""
    print("\nfiles   time (s)")
    for n in (10, 25, 51, 100, 200):
        batch = [SourceFile(k, "f%d.py" % k, files[k % len(files)].source) for k in range(n)]
        start = time.perf_counter()
        analyze(batch)
        print("%5d   %.3f" % (n, time.perf_counter() - start))
    print("(timing includes matching, scoring all n(n-1)/2 pairs and merge sort; parsing excluded)")


if __name__ == "__main__":
    files = load_folder(DATASET)
    ranked = analyze(files)
    accuracy_table(ranked)
    recall_by_variant(ranked)
    timing(files)
