"""Pretty-print an AST level by level (BFS).

Run:  python -m codeclone.ast_print some_file.py
"""

import sys

from .structures import Queue


def format_ast(root):
    lines = []
    queue = Queue()  # CO1: queue drives the level-order (BFS) traversal of the tree (CO3)
    queue.enqueue((root, 0, "-"))
    current_level = -1
    while not queue.is_empty():
        node, level, parent = queue.dequeue()
        if level != current_level:
            current_level = level
            lines.append("Level %d:" % level)
        lines.append("    %-34s (parent: %s)" % (repr(node), parent))
        for child in node.children:
            queue.enqueue((child, level + 1, node.label))
    return "\n".join(lines)


def print_ast(root):
    print(format_ast(root))


if __name__ == "__main__":
    from .parser import parse

    if len(sys.argv) != 2:
        sys.exit("usage: python -m codeclone.ast_print FILE.py")
    with open(sys.argv[1]) as f:
        print_ast(parse(f.read()))
