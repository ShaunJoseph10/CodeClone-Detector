"""Normalizer: erase identifier names and literal values so renamed copies look identical."""

from .structures import Stack

# Built-in calls keep their real name: print(...) vs range(...) is real structure, not a rename.
BUILTINS = ("print", "range", "len", "int", "str", "abs", "min", "max", "input")

# Operators whose operand order does not matter. The hasher sorts their children by hash,
# so a + b and b + a get the same fingerprint.
COMMUTATIVE = ("BinOp:+", "BinOp:*", "Compare:==", "Compare:!=", "BoolOp:and", "BoolOp:or")

# Mirrored comparisons are rewritten to one form: a > b -> b < a, a >= b -> b <= a.
FLIPPED = {"Compare:>": "Compare:<", "Compare:>=": "Compare:<="}


def normalize(root):
    """Rewrite node values in place:  variables/params -> VAR, user functions -> FUNC,
    numbers -> NUM, strings -> STR. Line numbers are kept for the report."""
    stack = Stack()  # CO1: explicit stack for an iterative walk over the tree (CO3)
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        if node.label in ("Name", "Param"):
            node.value = "VAR"
        elif node.label == "FunctionDef":
            node.value = "FUNC"
        elif node.label == "Call" and node.value not in BUILTINS:
            node.value = "FUNC"
        elif node.label == "Num":
            node.value = "NUM"
        elif node.label == "Str":
            node.value = "STR"
        elif node.label in FLIPPED:
            # a > b  is the same test as  b < a : rewrite so both spellings match
            node.label = FLIPPED[node.label]
            node.children.reverse()
        for child in node.children:
            stack.push(child)
    return root
