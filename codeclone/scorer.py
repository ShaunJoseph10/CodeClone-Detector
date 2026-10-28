"""Scorer: Dice similarity between two files from their clone pairs."""

from .hasher import M, P, string_hash
from .hashtable import HashMap
from .matcher import subtrees
from .structures import Stack
from .winnow import winnow_similarity


def covered_nodes(roots):
    """Number of distinct nodes inside the given subtrees (overlaps counted once)."""
    seen = set()
    for root in roots:
        for node in subtrees(root):
            seen.add(id(node))
    return len(seen)


def similarity(file_a, file_b, clones):
    """Dice coefficient: 2 * matched / (total_A + total_B).

    `matched` is averaged over both sides, (covered_A + covered_B) / 2, because one subtree
    in A may match several subtrees in B. Only clones between these two files are used."""
    mine = [c for c in clones if c.file_a is file_a and c.file_b is file_b]
    covered_a = covered_nodes([c.node_a for c in mine])
    covered_b = covered_nodes([c.node_b for c in mine])
    matched = (covered_a + covered_b) / 2
    return 2 * matched / (file_a.total_nodes + file_b.total_nodes)


# ---------------- v2 signals ----------------

STATEMENTS = ("Assign", "Expr", "Return", "Pass", "Break", "Continue", "If", "While", "For", "FunctionDef")
BLOCKS = ("Block", "Else")


def statement_hashes(node):
    """Flatten the statements under `node` into a pre-order list of HEADER hashes.
    A header is the statement without its nested blocks (e.g. `while VAR < VAR:`), so a
    junk line inserted inside a loop changes one entry instead of the whole loop."""
    out = []
    stack = Stack()  # CO1
    stack.push(node)
    while not stack.is_empty():
        n = stack.pop()
        if n.label in STATEMENTS:
            h = string_hash(n.label)
            for c in n.children:
                if c.label not in BLOCKS and c.label not in STATEMENTS:
                    h = (h * P + c.hash) % M
            out.append(h)
        for c in reversed(n.children):
            if c.label in BLOCKS or c.label in STATEMENTS:
                stack.push(c)
    return out


def units(file):
    """One statement sequence per top-level function, plus one for the module-level code."""
    if getattr(file, "_units", None) is None:
        funcs, top = [], []
        for stmt in file.root.children:
            if stmt.label == "FunctionDef":
                funcs.append(statement_hashes(stmt))
            else:
                top.extend(statement_hashes(stmt))
        # each unit is stored with a content key, so identical bodies share one LCS result
        file._units = [(_seq_key(u), u) for u in funcs + [top] if u]
    return file._units


def _seq_key(seq):
    h = len(seq)
    for x in seq:
        h = (h * P + x) % M
    return h


def lcs_length(a, b):
    """Longest common subsequence, dynamic programming with two rows. O(len(a) * len(b))."""
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, start=1):
            cur[j] = prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def _cached_lcs(ka, a, kb, b, cache):
    if ka == kb:
        return len(a)                  # identical bodies: no DP needed
    key = (ka, kb) if ka < kb else (kb, ka)
    value = cache.get(key)
    if value is None:
        value = lcs_length(a, b)
        cache.put(key, value)
    return value


def _covered_share(units_a, units_b, cache):
    """Share of A's statements found, in order, in the best-matching unit of B."""
    total = sum(len(u) for _, u in units_a)
    if total == 0:
        return 0.0
    found = 0
    for ka, u in units_a:
        found += max([_cached_lcs(ka, u, kb, v, cache) for kb, v in units_b] or [0])
    return found / total


def lcs_similarity(file_a, file_b, cache=None):
    """Each function is paired with its best match in the other file, so reordered
    functions still line up; inserted junk statements only cost the side that has them.
    Returns the mean of both directions."""
    cache = HashMap() if cache is None else cache  # CO4: (unit key, unit key) -> LCS length
    ua, ub = units(file_a), units(file_b)
    return (_covered_share(ua, ub, cache) + _covered_share(ub, ua, cache)) / 2


def signals(file_a, file_b, clones, fp_a, fp_b, cache=None):
    """All four signals for one pair, each in 0..1."""
    mine = [c for c in clones if c.file_a is file_a and c.file_b is file_b]
    cov_a = covered_nodes([c.node_a for c in mine])
    cov_b = covered_nodes([c.node_b for c in mine])
    return {
        "dice": (cov_a + cov_b) / (file_a.total_nodes + file_b.total_nodes),
        "containment": max(cov_a / file_a.total_nodes, cov_b / file_b.total_nodes),
        "lcs": lcs_similarity(file_a, file_b, cache),
        "winnow": winnow_similarity(fp_a, fp_b),
    }


def combine(sig, weights):
    """Weighted mean of the signals named in `weights`."""
    total = sum(weights.values())
    return sum(sig[k] * w for k, w in weights.items()) / total if total else 0.0
