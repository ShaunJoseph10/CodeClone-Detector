"""CodeClone Detector command line (v2, built on codeclone.api).

    python3 main.py <folder_of_.py_submissions> --threshold 0.6 --min-mass 6 [--json out.json]
"""

import argparse
import os
import sys

from codeclone.api import Config, analyze
from codeclone.matcher import MIN_MASS
from codeclone.report import print_summary, write_html


def load_folder(folder):
    """[(name, source)] for every .py file in the folder, sorted by name."""
    files = []
    for name in sorted(os.listdir(folder)):
        if name.endswith(".py"):
            with open(os.path.join(folder, name)) as f:
                files.append((name, f.read()))
    return files


def main():
    ap = argparse.ArgumentParser(description="Detect copied code between Python submissions.")
    ap.add_argument("folder")
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--min-mass", type=int, default=MIN_MASS)
    ap.add_argument("--out", default="report.html")
    ap.add_argument("--json", help="also write the full result as JSON")
    ap.add_argument("--v1", action="store_true", help="run the v1 engine (Dice only, all pairs)")
    args = ap.parse_args()

    if not os.path.isdir(args.folder):
        sys.exit("not a folder: %s" % args.folder)
    files = load_folder(args.folder)
    make = Config.v1 if args.v1 else Config
    result = analyze(files, make(threshold=args.threshold, min_mass=args.min_mass))
    for name, err in result.errors.items():
        print("skipping %s: %s" % (name, err), file=sys.stderr)
    if len(result.files) < 2:
        sys.exit("need at least 2 parsable .py files")

    write_html(args.out, result, dict(files))
    if args.json:
        with open(args.json, "w") as f:
            f.write(result.to_json(indent=1))
    print_summary(result)
    print("Report written to %s" % args.out)


if __name__ == "__main__":
    main()
