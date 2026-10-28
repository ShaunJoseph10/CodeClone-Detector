"""Normalizer: erase identifier names and literal values so renamed copies look identical."""

from .ast_nodes import Node
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


# ---------------- v2: canonical loop / assignment shapes ----------------

def _copy(node):
    """Deep copy of a small subtree (an assignment target such as a[i])."""
    return Node(node.label, node.value, [_copy(c) for c in node.children], node.start_line, node.end_line)


def _has_own_continue(block):
    """True if `continue` appears in this loop body (not counting nested loops / defs)."""
    stack = Stack()
    stack.push(block)
    while not stack.is_empty():
        node = stack.pop()
        if node.label == "Continue":
            return True
        for child in node.children:
            if child.label not in ("While", "For", "FunctionDef"):
                stack.push(child)
    return False


def _range_to_while(loop):
    """for v in range(a, b, s): body   ->   [v = a, while v < b: body; v = v + s]
    Returns the two new statements, or None when the loop is left alone:
      - not a range() call, or a step that is not a literal (its sign decides < vs >);
      - the body uses `continue`: it would jump over the appended increment and the
        while version would loop forever, so the rewrite would not be equivalent."""
    target, iterable, body = loop.children
    if iterable.label != "Call" or iterable.value != "range" or not 1 <= len(iterable.children) <= 3:
        return None
    if _has_own_continue(body):
        return None
    line, end = loop.start_line, loop.end_line
    args = iterable.children
    start = args[0] if len(args) >= 2 else Node("Num", 0, start_line=line, end_line=line)
    stop = args[1] if len(args) >= 2 else args[0]
    step, compare, step_op = Node("Num", 1, start_line=end, end_line=end), "Compare:<", "BinOp:+"
    if len(args) == 3:
        s = args[2]
        if s.label == "Num":
            step = s
        elif s.label == "UnaryOp:-" and s.children[0].label == "Num":
            step, compare, step_op = s.children[0], "Compare:>", "BinOp:-"
        else:
            return None

    def var(at):
        return Node("Name", target.value, start_line=at, end_line=at)

    init = Node("Assign", children=[var(line), start], start_line=line, end_line=line)
    bump = Node("Assign", children=[var(end), Node(step_op, children=[var(end), step], start_line=end, end_line=end)],
                start_line=end, end_line=end)
    body.children.append(bump)
    test = Node(compare, children=[var(line), stop], start_line=line, end_line=line)
    return [init, Node("While", children=[test, body], start_line=line, end_line=end)]


def canonicalize(root):
    """Rewrite equivalent spellings into one shape, in place:
       x += e          ->  x = x + e
       for v in range  ->  v = start; while v < stop: ...; v = v + step
    so for/while versions of the same loop hash the same."""
    stack = Stack()  # CO1: iterative walk over the tree (CO3)
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        new_children = []
        for child in node.children:
            if child.label.startswith("AugAssign:"):
                left, right = child.children
                op = child.label.split(":", 1)[1]
                child.label = "Assign"
                child.children = [left, Node("BinOp:" + op, children=[_copy(left), right],
                                             start_line=child.start_line, end_line=child.end_line)]
            if child.label == "For":
                rewritten = _range_to_while(child)
                if rewritten:
                    new_children.extend(rewritten)
                    continue
            new_children.append(child)
        node.children = new_children
        for child in node.children:
            stack.push(child)
    return root
