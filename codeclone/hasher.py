"""Hasher: fills node.size, node.hash and node.parent for every node (bottom-up).

hash(leaf) = H(label)
hash(node) = (H(label) * P^k + sum_{i=1..k} hash(child_i) * P^(k-i)) mod M
"""

from .normalizer import COMMUTATIVE
from .structures import Stack

P = 131
M = 2 ** 61 - 1


def node_key(node):
    """Text that identifies a node after normalization, e.g. "Name|VAR" or "BinOp:+"."""
    return node.label if node.value is None else node.label + "|" + str(node.value)


def string_hash(text):
    """CO4: polynomial rolling hash of a string. We do not use Python's hash(),
    because it is randomised between runs and the fingerprints must be stable."""
    h = 0
    for ch in text:
        h = (h * P + ord(ch)) % M
    return h


def hash_tree(root):
    """CO1: ITERATIVE post-order traversal with an explicit stack (no recursion).
    Each node is pushed twice: first to expand its children, then to compute its hash
    once all children are finished."""
    stack = Stack()
    stack.push((root, False))
    while not stack.is_empty():
        node, children_done = stack.pop()
        if not children_done:
            stack.push((node, True))
            for child in node.children:
                child.parent = node
                stack.push((child, False))
            continue

        # Commutative binary operator: put the smaller child hash first,
        # so a+b and b+a end up with identical child order (and identical hash).
        if node.label in COMMUTATIVE and node.children[0].hash > node.children[1].hash:
            node.children.reverse()

        k = len(node.children)
        h = string_hash(node_key(node)) * pow(P, k, M) % M   # CO4: tree fingerprint
        size = 1
        for i, child in enumerate(node.children, start=1):
            h = (h + child.hash * pow(P, k - i, M)) % M
            size += child.size
        node.hash = h
        node.size = size
    return root
