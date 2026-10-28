"""Scorer: Dice similarity between two files from their clone pairs."""

from .matcher import subtrees


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
