"""Matcher: find maximal identical (after normalization) subtrees shared by different files."""

from .hasher import hash_tree, node_key
from .hashtable import HashTable
from .normalizer import normalize
from .parser import parse
from .structures import Stack

MIN_MASS = 6


class SourceFile:
    """A parsed, normalized and hashed submission."""

    def __init__(self, file_id, name, source, passes=()):
        """passes: extra tree rewrites run before normalize(), e.g. (remove_dead_code, canonicalize)."""
        self.id = file_id
        self.name = name
        self.source = source
        root = parse(source)
        for rewrite in passes:
            root = rewrite(root)
        self.root = hash_tree(normalize(root))  # CO3 tree -> normalized -> hashed
        self.total_nodes = self.root.size


class Clone:
    """Two identical subtrees: node_a in file_a, node_b in file_b (file_a.id < file_b.id)."""

    def __init__(self, file_a, node_a, file_b, node_b):
        self.file_a, self.node_a = file_a, node_a
        self.file_b, self.node_b = file_b, node_b

    def as_tuple(self):
        """(fileA, linesA, fileB, linesB, size)"""
        return (self.file_a.name, (self.node_a.start_line, self.node_a.end_line),
                self.file_b.name, (self.node_b.start_line, self.node_b.end_line),
                self.node_a.size)


def subtrees(root):
    """All nodes of a tree, using an explicit stack (CO1) instead of recursion."""
    out = []
    stack = Stack()
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        out.append(node)
        for child in node.children:
            stack.push(child)
    return out


def structurally_equal(a, b):
    """True if the two trees are identical node by node. Guards against hash collisions."""
    stack = Stack()  # CO1: pairs of nodes still to compare
    stack.push((a, b))
    while not stack.is_empty():
        x, y = stack.pop()
        if node_key(x) != node_key(y) or len(x.children) != len(y.children):
            return False
        for cx, cy in zip(x.children, y.children):
            stack.push((cx, cy))
    return True


def find_clones(files, min_mass=MIN_MASS, allowed=None):
    """files: list of SourceFile. Returns the list of maximal Clone pairs between files.
    allowed: optional HashSet of (id_a, id_b) file pairs; other pairs are not verified."""
    # 1. Insert every subtree of at least min_mass nodes into our own hash table (CO4).
    table = HashTable()
    for f in files:
        for node in subtrees(f.root):
            if node.size >= min_mass:
                table.insert(node.hash, f, node)

    # 2. Inside each bucket, group entries into classes of truly identical subtrees.
    #    3. Verify: equal hash is not proof, so each entry is compared with ONE representative
    #    per class (O(b) checks per bucket instead of O(b^2)); equality is transitive.
    candidates = []
    matched = set()  # (id(node_a), id(node_b)) of every verified match, for the maximal check
    for chain in table.chains():
        classes = []  # [representative entry, members...]
        for e in chain:
            for cls in classes:
                if cls[0].fingerprint == e.fingerprint and structurally_equal(cls[0].node, e.node):
                    cls.append(e)
                    break
            else:
                classes.append([e])
        for cls in classes:
            for i in range(len(cls)):
                for j in range(i + 1, len(cls)):
                    x, y = cls[i], cls[j]
                    if x.file_id is y.file_id:
                        continue
                    if x.file_id.id > y.file_id.id:
                        x, y = y, x
                    if allowed is not None and (x.file_id.id, y.file_id.id) not in allowed:
                        continue
                    candidates.append(Clone(x.file_id, x.node, y.file_id, y.node))
                    matched.add((id(x.node), id(y.node)))

    # 4. Keep only maximal clones: drop a match if the two parents also match.
    clones = []
    for c in candidates:
        pa, pb = c.node_a.parent, c.node_b.parent
        if pa is not None and pb is not None and (id(pa), id(pb)) in matched:
            continue
        clones.append(c)
    return clones
