"""Phase 1 tests: lexer, parser, AST printer.   Run: python -m unittest discover tests"""

import unittest

from codeclone.ast_print import format_ast
from codeclone.lexer import LexerError, tokenize
from codeclone.parser import ParseError, parse

FACTORIAL = """
# recursive factorial
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""

PRIMES = """
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i = i + 1
    return True

for k in range(2, 30):
    if is_prime(k):
        print(k)
"""

BUBBLE_SORT = """
def bubble_sort(arr, n):
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
    return arr

data = [5, 1, 4, 2, 8]
print(bubble_sort(data, 5))
"""

GCD = """
def gcd(a, b):
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

print("gcd is", gcd(48, 18))
"""

FIBONACCI = """
def fib(n):
    a = 0
    b = 1
    count = 0
    while count < n and not a > 1000:
        print(a)
        c = a + b
        a = b
        b = c
        count += 1
    return a

fib(10)
"""

SAMPLES = {"factorial": FACTORIAL, "primes": PRIMES, "bubble_sort": BUBBLE_SORT,
           "gcd": GCD, "fibonacci": FIBONACCI}


def expr_of(src):
    """Parse a single expression statement and return the expression subtree."""
    return parse(src + "\n").children[0].children[0]


def to_text(node):
    """Fully parenthesised text form of an expression tree, used to check precedence."""
    if not node.children:
        return str(node.value)
    op = node.label.split(":", 1)[1] if ":" in node.label else node.label
    if len(node.children) == 1:
        return "(%s %s)" % (op, to_text(node.children[0]))
    return "(%s %s %s)" % (to_text(node.children[0]), op, to_text(node.children[1]))


class TestSamples(unittest.TestCase):
    def test_all_samples_parse_and_print(self):
        for name, src in SAMPLES.items():
            with self.subTest(program=name):
                root = parse(src)
                self.assertEqual(root.label, "Module")
                self.assertTrue(root.children)
                self.assertIn("Level 0:", format_ast(root))

    def test_factorial_structure(self):
        root = parse(FACTORIAL)
        func = root.children[0]
        self.assertEqual((func.label, func.value), ("FunctionDef", "factorial"))
        self.assertEqual((func.start_line, func.end_line), (3, 6))
        self.assertEqual(func.children[0].children[0].value, "n")  # parameter
        ret = func.children[1].children[1]
        self.assertEqual(ret.label, "Return")
        self.assertEqual(ret.children[0].label, "BinOp:*")


class TestLexer(unittest.TestCase):
    def test_indent_dedent_balanced(self):
        types = [t.type for t in tokenize(FACTORIAL)]
        self.assertEqual(types.count("INDENT"), types.count("DEDENT"))

    def test_inconsistent_dedent(self):
        with self.assertRaises(LexerError):
            tokenize("if x:\n        y = 1\n    z = 2\n")

    def test_unbalanced_parens(self):
        with self.assertRaises(LexerError):
            tokenize("print((1 + 2)\n")
        with self.assertRaises(LexerError):
            tokenize("x = (1 + 2))\n")
        with self.assertRaises(LexerError):
            tokenize("x = (1 + 2]\n")

    def test_comments_ignored(self):
        values = [t.value for t in tokenize("x = 1  # set x\n# whole line\n")]
        self.assertNotIn("#", "".join(str(v) for v in values))


class TestExpressions(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(to_text(expr_of("1 + 2 * 3")), "(1 + (2 * 3))")
        self.assertEqual(to_text(expr_of("(1 + 2) * 3")), "((1 + 2) * 3)")
        self.assertEqual(to_text(expr_of("a - b - c")), "((a - b) - c)")
        self.assertEqual(to_text(expr_of("a < b and b < c or d")), "(((a < b) and (b < c)) or d)")

    def test_unary(self):
        self.assertEqual(to_text(expr_of("-a * b")), "((- a) * b)")
        self.assertEqual(to_text(expr_of("not a == b")), "(not (a == b))")
        self.assertEqual(to_text(expr_of("a and not b")), "(a and (not b))")
        self.assertEqual(to_text(expr_of("- - 3")), "(- (- 3))")

    def test_parse_errors(self):
        for bad in ["x = 1 +\n", "def f(1):\n    pass\n", "if x\n    y = 1\n", "1 = x\n"]:
            with self.subTest(src=bad), self.assertRaises(ParseError):
                parse(bad)


if __name__ == "__main__":
    unittest.main()
