"""Parser: tokens -> AST.

Statements and blocks use recursive descent.
Expressions use the SHUNTING-YARD algorithm (operator stack -> postfix list),
then the tree is built from the postfix list with an operand stack.
"""

from .ast_nodes import Node
from .lexer import tokenize
from .structures import Stack


class ParseError(Exception):
    pass


# Binary operator precedence (higher binds tighter) and node label prefix.
BINARY = {
    "or": (1, "BoolOp"), "and": (2, "BoolOp"),
    "==": (4, "Compare"), "!=": (4, "Compare"), "<": (4, "Compare"),
    ">": (4, "Compare"), "<=": (4, "Compare"), ">=": (4, "Compare"),
    "+": (5, "BinOp"), "-": (5, "BinOp"),
    "*": (6, "BinOp"), "/": (6, "BinOp"), "//": (6, "BinOp"), "%": (6, "BinOp"),
}
# Unary (prefix) operators. "neg" is unary minus. Both are right-associative.
UNARY = {"not": 3, "neg": 7}

AUG_OPS = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.last_line = 1  # line of the most recently consumed token

    # ---------- token helpers ----------
    def peek(self, offset=0):
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def check(self, type_, value=None):
        tok = self.peek()
        return tok.type == type_ and (value is None or tok.value == value)

    def advance(self):
        tok = self.peek()
        self.pos += 1
        if tok.type not in ("NEWLINE", "INDENT", "DEDENT", "EOF"):
            self.last_line = tok.line
        return tok

    def expect(self, type_, value=None):
        if not self.check(type_, value):
            tok = self.peek()
            want = value if value is not None else type_
            raise ParseError("line %d: expected %r but found %r" % (tok.line, want, tok.value or tok.type))
        return self.advance()

    # ---------- statements (recursive descent) ----------
    def parse_module(self):
        body = []
        while not self.check("EOF"):
            body.append(self.parse_statement())
        end = body[-1].end_line if body else 0
        return Node("Module", children=body, start_line=1 if body else 0, end_line=end)

    def parse_block(self):
        """':' NEWLINE INDENT statement+ DEDENT"""
        self.expect("OP", ":")
        self.expect("NEWLINE")
        self.expect("INDENT")
        start = self.peek().line
        stmts = []
        while not self.check("DEDENT") and not self.check("EOF"):
            stmts.append(self.parse_statement())
        self.expect("DEDENT")
        return Node("Block", children=stmts, start_line=start, end_line=self.last_line)

    def parse_statement(self):
        tok = self.peek()
        if tok.type == "KEYWORD":
            if tok.value == "def":
                return self.parse_def()
            if tok.value == "if":
                return self.parse_if()
            if tok.value == "while":
                return self.parse_while()
            if tok.value == "for":
                return self.parse_for()
            if tok.value == "return":
                self.advance()
                children = [] if self.check("NEWLINE") else [self.parse_expr()]
                self.expect("NEWLINE")
                return Node("Return", children=children, start_line=tok.line, end_line=self.last_line)
            if tok.value in ("pass", "break", "continue"):
                self.advance()
                self.expect("NEWLINE")
                return Node(tok.value.capitalize(), start_line=tok.line, end_line=tok.line)
        return self.parse_simple()

    def parse_def(self):
        start = self.expect("KEYWORD", "def").line
        name = self.expect("NAME").value
        self.expect("OP", "(")
        params = []
        while not self.check("OP", ")"):
            p = self.expect("NAME")
            params.append(Node("Param", p.value, start_line=p.line, end_line=p.line))
            if not self.check("OP", ")"):
                self.expect("OP", ",")
        self.expect("OP", ")")
        params_node = Node("Params", children=params, start_line=start, end_line=start)
        body = self.parse_block()
        return Node("FunctionDef", name, [params_node, body], start, self.last_line)

    def parse_if(self):
        # 'if' and 'elif' share this code; elif becomes a nested If in the else branch.
        start = self.advance().line
        cond = self.parse_expr()
        body = self.parse_block()
        children = [cond, body]
        if self.check("KEYWORD", "elif"):
            children.append(self.parse_if())
        elif self.check("KEYWORD", "else"):
            self.advance()
            else_block = self.parse_block()
            else_block.label = "Else"
            children.append(else_block)
        return Node("If", children=children, start_line=start, end_line=self.last_line)

    def parse_while(self):
        start = self.expect("KEYWORD", "while").line
        cond = self.parse_expr()
        body = self.parse_block()
        return Node("While", children=[cond, body], start_line=start, end_line=self.last_line)

    def parse_for(self):
        start = self.expect("KEYWORD", "for").line
        var = self.expect("NAME")
        target = Node("Name", var.value, start_line=var.line, end_line=var.line)
        self.expect("KEYWORD", "in")
        iterable = self.parse_expr()
        body = self.parse_block()
        return Node("For", children=[target, iterable, body], start_line=start, end_line=self.last_line)

    def parse_simple(self):
        """Assignment (x = e, x[i] = e, x += e) or a bare expression such as print(x)."""
        start = self.peek().line
        left = self.parse_expr()
        if self.check("OP", "="):
            if left.label not in ("Name", "Subscript"):
                raise ParseError("line %d: cannot assign to %s" % (start, left.label))
            self.advance()
            right = self.parse_expr()
            node = Node("Assign", children=[left, right], start_line=start)
        elif self.check("OP") and self.peek().value in AUG_OPS:
            op = AUG_OPS[self.advance().value]
            right = self.parse_expr()
            node = Node("AugAssign:" + op, children=[left, right], start_line=start)
        else:
            node = Node("Expr", children=[left], start_line=start)
        self.expect("NEWLINE")
        node.end_line = self.last_line
        return node

    # ---------- expressions (shunting-yard) ----------
    def parse_expr(self):
        """Read one expression and return its subtree.

        Atoms (names, literals, calls, subscripts, lists) are read directly and
        go straight to the output. Operators and '(' go through the operator stack.
        """
        output = []           # postfix list: Nodes (operands) and operator strings
        ops = Stack()         # CO1: operator stack of the shunting-yard algorithm
        expect_operand = True
        depth = 0             # open grouping parentheses inside this expression

        while True:
            tok = self.peek()
            if expect_operand:
                if tok.type == "KEYWORD" and tok.value == "not":
                    self.advance()
                    ops.push("not")  # prefix operator: pushed without popping anything
                elif tok.type == "OP" and tok.value == "-":
                    self.advance()
                    ops.push("neg")
                elif tok.type == "OP" and tok.value == "(":
                    self.advance()
                    ops.push("(")
                    depth += 1
                else:
                    output.append(self.parse_atom())
                    expect_operand = False
            else:
                is_binop = (tok.type == "OP" or tok.type == "KEYWORD") and tok.value in BINARY
                if is_binop:
                    self.advance()
                    prec = BINARY[tok.value][0]
                    # Pop operators that bind at least as tightly (all binaries are left-assoc).
                    while not ops.is_empty() and ops.peek() != "(" and self._prec(ops.peek()) >= prec:
                        output.append(ops.pop())
                    ops.push(tok.value)
                    expect_operand = True
                elif tok.type == "OP" and tok.value == ")" and depth > 0:
                    self.advance()
                    while ops.peek() != "(":
                        output.append(ops.pop())
                    ops.pop()  # discard '('
                    depth -= 1
                else:
                    break  # anything else ends the expression (NEWLINE, ':', ',', '=', ...)

        if expect_operand:
            tok = self.peek()
            raise ParseError("line %d: expected an expression but found %r" % (tok.line, tok.value or tok.type))
        if depth > 0:
            raise ParseError("line %d: missing ')' in expression" % self.peek().line)
        while not ops.is_empty():
            output.append(ops.pop())
        return self._build_tree(output)

    @staticmethod
    def _prec(op):
        return UNARY[op] if op in UNARY else BINARY[op][0]

    @staticmethod
    def _build_tree(postfix):
        """Turn the postfix list into a tree. CO1: operand stack. CO3: builds the subtree."""
        stack = Stack()
        for item in postfix:
            if isinstance(item, Node):
                stack.push(item)
            elif item in UNARY:
                operand = stack.pop()
                label = "UnaryOp:not" if item == "not" else "UnaryOp:-"
                stack.push(Node(label, children=[operand],
                                start_line=operand.start_line, end_line=operand.end_line))
            else:
                right = stack.pop()
                left = stack.pop()
                label = BINARY[item][1] + ":" + item
                stack.push(Node(label, children=[left, right],
                                start_line=left.start_line, end_line=right.end_line))
        return stack.pop()

    def parse_atom(self):
        tok = self.advance()
        if tok.type == "NUM":
            node = Node("Num", tok.value, start_line=tok.line, end_line=tok.line)
        elif tok.type == "STR":
            node = Node("Str", tok.value, start_line=tok.line, end_line=tok.line)
        elif tok.type == "KEYWORD" and tok.value in ("True", "False", "None"):
            node = Node("Const", tok.value, start_line=tok.line, end_line=tok.line)
        elif tok.type == "OP" and tok.value == "[":
            items = self.parse_arguments("]")
            node = Node("List", children=items, start_line=tok.line, end_line=self.last_line)
        elif tok.type == "NAME":
            if self.check("OP", "("):
                self.advance()
                args = self.parse_arguments(")")
                node = Node("Call", tok.value, args, tok.line, self.last_line)
            else:
                node = Node("Name", tok.value, start_line=tok.line, end_line=tok.line)
        else:
            raise ParseError("line %d: unexpected %r" % (tok.line, tok.value or tok.type))

        # Subscripts such as a[i] or grid[i][j]
        while self.check("OP", "["):
            self.advance()
            index = self.parse_expr()
            self.expect("OP", "]")
            node = Node("Subscript", children=[node, index], start_line=node.start_line, end_line=self.last_line)
        return node

    def parse_arguments(self, closer):
        """Comma-separated expressions up to `closer`; the closer is consumed."""
        items = []
        while not self.check("OP", closer):
            items.append(self.parse_expr())
            if not self.check("OP", closer):
                self.expect("OP", ",")
        self.expect("OP", closer)
        return items


def parse(source):
    """Source text -> root Node("Module")."""
    return Parser(tokenize(source)).parse_module()
