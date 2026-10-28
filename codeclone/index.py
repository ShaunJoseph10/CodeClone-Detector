"""Candidate generation with an INVERTED INDEX: fingerprint -> linked list of file ids.

Instead of scoring all n(n-1)/2 pairs, only pairs that share at least `min_shared`
fingerprints are scored. Fingerprints found in more than `max_df` of the files are
common boilerplate (e.g. print(VAR)) and are ignored.
"""

from .hashtable import HashMap


class Posting:
    """One cell of a posting list (CO2: singly linked list of file ids)."""

    def __init__(self, file_id, next_):
        self.file_id = file_id
        self.next = next_


def build_index(fp_sets):
    """fp_sets[i]: HashSet of file i's fingerprints. Returns HashMap fp -> (head, length)."""
    index = HashMap()  # CO4
    for file_id, fps in enumerate(fp_sets):
        for h in fps:
            head, length = index.get(h, (None, 0))
            index.put(h, (Posting(file_id, head), length + 1))  # CO2: push at the head
    return index


def candidate_pairs(fp_sets, min_shared=3, max_df=0.5):
    """Returns (pairs, ignored_fingerprints). pairs: sorted list of (i, j), i < j.
    A file with fewer than min_shared fingerprints only needs to share all of them."""
    n = len(fp_sets)
    index = build_index(fp_sets)
    shared = HashMap()  # (i, j) -> number of shared fingerprints
    ignored = 0
    limit = max(2, max_df * n)
    for _, (head, length) in index.items():
        if length > limit:
            ignored += 1
            continue
        ids = []
        cell = head
        while cell is not None:  # CO2: walk the posting list
            ids.append(cell.file_id)
            cell = cell.next
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                key = (min(ids[x], ids[y]), max(ids[x], ids[y]))
                shared.put(key, shared.get(key, 0) + 1)
    pairs = [key for key, count in shared.items()
             if count >= min(min_shared, len(fp_sets[key[0]]), len(fp_sets[key[1]]))]
    return pairs, ignored
