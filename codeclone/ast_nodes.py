"""AST node definition (CO3: the program is represented as a tree)."""


class Node:
    """One node of the abstract syntax tree.

    label      kind of node, e.g. "Assign", "If", "BinOp:+", "Name", "Num"
    value      extra data (variable name, number, function name) or None
    children   list of child Nodes (CO3: n-ary tree)
    start_line / end_line   source lines this node covers
    size, hash, parent filled in later by the hasher (Phase 2)
    """

    def __init__(self, label, value=None, children=None, start_line=0, end_line=0):
        self.label = label
        self.value = value
        self.children = children if children is not None else []
        self.start_line = start_line
        self.end_line = end_line
        self.size = 0
        self.hash = 0
        self.parent = None

    def __repr__(self):
        text = self.label if self.value is None else "%s(%r)" % (self.label, self.value)
        return "%s [%d-%d]" % (text, self.start_line, self.end_line)
