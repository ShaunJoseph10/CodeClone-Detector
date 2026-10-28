"""Dead-code normalization: delete code that can never run or whose result is never used,
so a copy padded with junk statements looks like the original again.

Runs on the raw AST (real names), before canonicalize() and normalize().

1. Constant conditions: inside one block, variables assigned a literal are tracked; an
   `if` whose test folds to False is replaced by its else branch (True -> its body), and a
   `while` whose test is False on entry is deleted.  `if False:` is the trivial case.
2. Unreachable code: statements after return / break / continue in the same block.
3. Liveness (functions only): a backward pass deletes `x = e` when x is never read
   afterwards and e contains no call (a call might have side effects).
"""

from .hashtable import HashMap, HashSet
from .structures import Stack

SIMPLE = ("Assign", "Expr", "Return", "Pass", "Break", "Continue")
COMPOUND = ("If", "While", "For")
UNKNOWN = object()  # "not a compile-time constant"


def fold(node, env):
    """Value of an expression if it is a compile-time constant, else UNKNOWN.
    env: HashMap name -> constant value for variables known at this point."""
    label = node.label
    if label in ("Num", "Str"):
        return node.value
    if label == "Const":
        return {"True": True, "False": False, "None": None}[node.value]
    if label == "Name":
        return env.get(node.value, UNKNOWN)
    if label == "List":
        items = tuple(fold(c, env) for c in node.children)
        return UNKNOWN if UNKNOWN in items else items
    if label == "Call" and node.value == "len" and len(node.children) == 1:
        v = fold(node.children[0], env)
        return len(v) if isinstance(v, (tuple, str)) else UNKNOWN
    if label.startswith(("BinOp:", "Compare:", "BoolOp:", "UnaryOp:")):
        vals = [fold(c, env) for c in node.children]
        if UNKNOWN in vals:
            return UNKNOWN
        try:
            return _apply(label.split(":", 1)[1], vals)
        except (TypeError, ZeroDivisionError, ValueError):
            return UNKNOWN
    return UNKNOWN


def _apply(op, vals):
    if len(vals) == 1:
        return (not vals[0]) if op == "not" else -vals[0]
    a, b = vals
    ops = {
        "+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b,
        "//": lambda: a // b, "%": lambda: a % b,
        "==": lambda: a == b, "!=": lambda: a != b, "<": lambda: a < b, ">": lambda: a > b,
        "<=": lambda: a <= b, ">=": lambda: a >= b,
        "and": lambda: a and b, "or": lambda: a or b,
    }
    return ops[op]()


def names_in(node, labels=("Name",)):
    """Names of every Name node in a subtree (iterative walk, CO1)."""
    out = []
    stack = Stack()
    stack.push(node)
    while not stack.is_empty():
        n = stack.pop()
        if n.label in labels:
            out.append(n.value)
        for c in n.children:
            stack.push(c)
    return out


def has_call(node):
    stack = Stack()
    stack.push(node)
    while not stack.is_empty():
        n = stack.pop()
        if n.label == "Call":
            return True
        for c in n.children:
            stack.push(c)
    return False


def assigned_in(node):
    """Variables that may be written anywhere inside a statement."""
    out = []
    stack = Stack()
    stack.push(node)
    while not stack.is_empty():
        n = stack.pop()
        if (n.label == "Assign" or n.label.startswith("AugAssign")) and n.children[0].label == "Name":
            out.append(n.children[0].value)
        elif n.label == "For":
            out.append(n.children[0].value)
        for c in n.children:
            stack.push(c)
    return out


# ---------------- 1 + 2: constant conditions and unreachable code ----------------

def _simplify_block(block):
    """Rewrite block.children in place. CO1: a stack holds statements still to process,
    so a removed `if` can splice its surviving branch back in front."""
    env = HashMap()  # CO4: name -> known constant value
    todo = Stack()
    for stmt in reversed(block.children):
        todo.push(stmt)
    out = []
    while not todo.is_empty():
        stmt = todo.pop()
        label = stmt.label
        if label in ("If", "While"):
            test = fold(stmt.children[0], env)
            if test is not UNKNOWN and not test:
                if label == "If" and len(stmt.children) == 3:   # keep the else / elif branch
                    rest = stmt.children[2]
                    branch = [rest] if rest.label == "If" else rest.children
                    for s in reversed(branch):
                        todo.push(s)
                continue                                         # dead branch / loop removed
            if label == "If" and test is not UNKNOWN:           # always true: keep the body
                for s in reversed(stmt.children[1].children):
                    todo.push(s)
                continue
        out.append(stmt)

        if label == "Assign" and stmt.children[0].label == "Name":
            value = fold(stmt.children[1], env)
            if value is UNKNOWN:
                env.remove(stmt.children[0].value)
            else:
                env.put(stmt.children[0].value, value)
        else:
            for name in assigned_in(stmt):
                env.remove(name)
            if label == "Assign" or has_call(stmt):
                # a call or a[i] = ... may change a list in place: forget known lists
                for name, value in list(env.items()):
                    if isinstance(value, tuple):
                        env.remove(name)

        if label in COMPOUND or label == "FunctionDef":
            for child in stmt.children:
                _simplify_child(child)
        if label in ("Return", "Break", "Continue"):
            break                                                # the rest is unreachable
    block.children = out


def _simplify_child(node):
    if node.label in ("Block", "Else"):
        _simplify_block(node)
    elif node.label == "If":       # elif chain
        for child in node.children:
            _simplify_child(child)


# ---------------- 3: liveness (backward pass) ----------------

def _prune_block(block, live):
    """Walk the statements BACKWARDS. `live` = variables read later (a HashSet, CO4).
    Returns the live set at the start of the block."""
    kept = []
    for stmt in reversed(block.children):
        if stmt.label == "Assign" and stmt.children[0].label == "Name":
            target, value = stmt.children
            if target.value not in live and not has_call(value):
                continue                        # dead store: never read afterwards
            live.discard(target.value)
            live.update(names_in(value))
        elif stmt.label in COMPOUND:
            # Conservative for branches and loops: everything read anywhere inside the
            # statement counts as live inside it (a loop can read a value on the next turn).
            live.update(names_in(stmt))
            for child in stmt.children:
                _prune_child(child, live)
        elif stmt.label != "FunctionDef":
            live.update(names_in(stmt))
        kept.append(stmt)
    kept.reverse()
    block.children = kept
    return live


def _prune_child(node, live):
    if node.label in ("Block", "Else"):
        _prune_block(node, live.copy())
    elif node.label == "If":
        for child in node.children:
            _prune_child(child, live)


def remove_dead_code(root):
    """Apply all three rules to a Module tree in place and return it."""
    _simplify_block(root)
    stack = Stack()
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        if node.label == "FunctionDef":
            _prune_block(node.children[1], HashSet())   # locals die when the function returns
        for child in node.children:
            stack.push(child)
    return root
