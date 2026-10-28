"""Evaluate the detector on dataset/: v1 vs v2 accuracy, per-disguise recall, timing.

Ground truth comes from file names: pX_<program>_<variant>.py.
Two files are a true plagiarism pair when they share the same program prefix and neither is
the "different" variant (a different algorithm for the same task is not a copy).

    python3 evaluate.py          # full report
    python3 evaluate.py --tune   # also grid-search the signal weights
"""

import itertools
import sys
import time

from codeclone.api import Config, analyze
from main import load_folder

DATASET = "dataset"
THRESHOLDS = (0.4, 0.5, 0.6, 0.7, 0.8)


def program_of(name):
    """'p3_bubble_renamed.py' -> 'p3_bubble'; unrelated or 'different' files -> None."""
    if not name.startswith("p") or name.endswith("_different.py"):
        return None
    return "_".join(name.split("_")[:2])


def is_plagiarism(a, b):
    pa, pb = program_of(a), program_of(b)
    return pa is not None and pa == pb


def positives(names):
    return sum(1 for a, b in itertools.combinations(names, 2) if is_plagiarism(a, b))


def metrics(result, threshold):
    """(flagged, tp, fp, fn, precision, recall, f1). Pairs the index skipped count as 'not flagged'."""
    pos = positives(result.files)
    flagged = [p for p in result.pairs if p.score >= threshold]
    tp = sum(1 for p in flagged if is_plagiarism(p.a, p.b))
    fp, fn = len(flagged) - tp, pos - tp
    precision = tp / len(flagged) if flagged else 1.0
    recall = tp / pos if pos else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return len(flagged), tp, fp, fn, precision, recall, f1


def accuracy_table(title, result):
    print("\n%s: %d files, %d true plagiarism pairs, %d pairs scored, %d skipped"
          % (title, len(result.files), positives(result.files),
             result.stats["pairs_scored"], result.stats["pairs_skipped"]))
    print("threshold  flagged   TP   FP   FN  precision  recall    F1")
    for t in THRESHOLDS:
        n, tp, fp, fn, p, r, f1 = metrics(result, t)
        print("   %.1f      %4d  %4d %4d %4d     %.3f    %.3f  %.3f" % (t, n, tp, fp, fn, p, r, f1))


def recall_by_variant(result, threshold=0.6):
    """Detection rate of each disguise against its own original: {variant: (hit, total)}."""
    scores = {(p.a, p.b): p.score for p in result.pairs}
    stats = {}
    for orig in result.files:
        if not orig.endswith("_original.py"):
            continue
        prefix = orig[:-len("original.py")]
        for other in result.files:
            if other == orig or not other.startswith(prefix) or other.endswith("_different.py"):
                continue
            key = (orig, other) if orig < other else (other, orig)
            variant = other[len(prefix):-3]
            hit, total = stats.get(variant, (0, 0))
            stats[variant] = (hit + (scores.get(key, 0.0) >= threshold), total + 1)
    return stats


def timing():
    """Running time vs number of files. Larger inputs are made by repeating the dataset."""
    base = load_folder(DATASET)
    print("\nfiles   v1 time (s)   v2 time (s)   v2 pairs scored / total")
    for n in (50, 200, 500):
        batch = [("f%d.py" % k, base[k % len(base)][1]) for k in range(n)]
        t = time.perf_counter()
        analyze(batch, Config.v1())
        v1 = time.perf_counter() - t
        t = time.perf_counter()
        r = analyze(batch, Config())
        v2 = time.perf_counter() - t
        print("%5d   %10.3f   %10.3f   %d / %d" % (n, v1, v2, r.stats["pairs_scored"], r.stats["total_pairs"]))
    print("(full pipeline: parsing, passes, fingerprints, index, matching, scoring, ranking)")


def tune(files):
    """Grid-search the weights; rank by F1 at 0.6, then by the gap between the lowest true
    pair and the highest false pair (a wider gap = more robust threshold)."""
    print("\nWeight tuning (dice, containment, lcs, winnow):")
    rows = []
    steps = (0.0, 0.1, 0.2, 0.3, 0.4)
    for w in itertools.product(steps, repeat=4):
        if abs(sum(w) - 1.0) > 1e-9:
            continue
        weights = dict(zip(("dice", "containment", "lcs", "winnow"), w))
        r = analyze(files, Config(weights=weights))
        true = [p.score for p in r.pairs if is_plagiarism(p.a, p.b)]
        false = [p.score for p in r.pairs if not is_plagiarism(p.a, p.b)] or [0.0]
        rows.append((metrics(r, 0.6)[6], min(true) - max(false), w))
    rows.sort(reverse=True)
    for f1, gap, w in rows[:5]:
        print("  %s  F1=%.3f  gap=%.3f" % (w, f1, gap))


def main():
    files = load_folder(DATASET)
    v1 = analyze(files, Config.v1())
    v2 = analyze(files, Config())
    accuracy_table("v1 (Dice only, all pairs)", v1)
    accuracy_table("v2 (passes + 4 signals + index)", v2)

    print("\nPer disguise, original vs variant at threshold 0.6 (detected / total):")
    print("  disguise          v1      v2")
    s1, s2 = recall_by_variant(v1), recall_by_variant(v2)
    for variant in s2:
        print("  %-14s  %d / %d   %d / %d" % ((variant,) + s1[variant] + s2[variant]))

    m1, m2 = metrics(v1, 0.6), metrics(v2, 0.6)
    print("\nv1 vs v2 at threshold 0.6:")
    print("              v1      v2")
    for label, k in (("precision", 4), ("recall", 5), ("F1", 6)):
        print("  %-10s %.3f   %.3f" % (label, m1[k], m2[k]))
    timing()
    if "--tune" in sys.argv:
        tune(files)


if __name__ == "__main__":
    main()
