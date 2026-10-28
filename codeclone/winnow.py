"""Winnowing fingerprints (Schleimer, Wilkerson, Aiken 2003 - the MOSS algorithm).

Token stream = pre-order node keys of the normalized tree, so renaming, for/while and
dead-code disguises are already removed before fingerprinting.
  1. k-grams of consecutive tokens, hashed with a ROLLING polynomial hash (CO4): O(n).
  2. Slide a window of w k-gram hashes; keep the minimum of each window (rightmost on ties).
Any shared run of at least w + k - 1 tokens is guaranteed to share a fingerprint.
"""

from .hasher import M, P, node_key, string_hash
from .hashtable import HashSet
from .structures import Stack

K = 5
WINDOW = 4


def token_stream(root):
    """[(token_hash, line)] in pre-order, using an explicit stack (CO1)."""
    out = []
    stack = Stack()
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        out.append((string_hash(node_key(node)), node.start_line))
        for child in reversed(node.children):
            stack.push(child)
    return out


def kgram_hashes(tokens, k=K):
    """Rolling hash: h(i+1) = (h(i) - t_i * P^(k-1)) * P + t_(i+k)   (mod M)."""
    if len(tokens) < k:
        k = len(tokens)
    if k == 0:
        return []
    top = pow(P, k - 1, M)
    h = 0
    for t, _ in tokens[:k]:
        h = (h * P + t) % M
    out = [(h, tokens[0][1])]
    for i in range(k, len(tokens)):
        h = ((h - tokens[i - k][0] * top) * P + tokens[i][0]) % M
        out.append((h, tokens[i - k + 1][1]))
    return out


def winnow(grams, w=WINDOW):
    """Window-minimum selection. Returns [(hash, line)] fingerprints in file order."""
    if not grams:
        return []
    w = min(w, len(grams))
    picked = []
    last = -1
    for start in range(len(grams) - w + 1):
        best = start
        for i in range(start, start + w):
            if grams[i][0] <= grams[best][0]:
                best = i                    # rightmost minimum
        if best != last:                    # record each chosen position once
            picked.append(grams[best])
            last = best
    return picked


def fingerprints(root, k=K, w=WINDOW):
    return winnow(kgram_hashes(token_stream(root), k), w)


def fingerprint_set(prints):
    return HashSet(h for h, _ in prints)


def winnow_similarity(set_a, set_b):
    """Shared fingerprints / fingerprints of the smaller file (containment, 0..1)."""
    if not len(set_a) or not len(set_b):
        return 0.0
    small, big = (set_a, set_b) if len(set_a) <= len(set_b) else (set_b, set_a)
    shared = sum(1 for h in small if h in big)
    return shared / len(small)
